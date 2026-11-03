using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace StoryboardAIStudio
{
    static class Program
    {
        private static readonly string AppTitle = "Storyboard AI Studio Pro";
        private static Mutex singleInstanceMutex = null;
        private static Process pythonProcess = null;
        private static NotifyIcon trayIcon = null;
        private static string baseDir = "";
        private static string studioDir = "";
        private static volatile bool shuttingDown = false;
        private static volatile bool uiPresented = false;
        private static readonly object backendLock = new object();
        private static System.Threading.Timer backendTimer = null;
        private static int backendFailures = 0;
        private static DateTime restartWindow = DateTime.UtcNow;
        private static EventWaitHandle openRequest = null;
        private const string OpenEventName = @"Local\StoryboardAIStudioPro_OpenWindow_2026";

        [DllImport("user32.dll", CharSet=CharSet.Unicode)]
        private static extern int GetWindowText(IntPtr hwnd, System.Text.StringBuilder text, int max);
        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hwnd);
        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hwnd, int nCmdShow);
        [DllImport("user32.dll")]
        private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
        private delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr lParam);


        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            bool isNewInstance;
            singleInstanceMutex = new Mutex(true, "StoryboardAIStudioPro_SingleInstance_Mutex_2026", out isNewInstance);
            if (!isNewInstance)
            {
                // Do not open the default web browser or a second Edge window.
                // Signal the existing Studio launcher to bring back its one UI.
                try
                {
                    using (var e = EventWaitHandle.OpenExisting(OpenEventName))
                        e.Set();
                }
                catch { }
                return;
            }
            openRequest = new EventWaitHandle(false, EventResetMode.AutoReset, OpenEventName);
            ThreadPool.QueueUserWorkItem(delegate(object state) {
                while (!shuttingDown)
                {
                    try
                    {
                        if (openRequest.WaitOne(1000) && BackendHealthy())
                            OpenStudioWindow();
                    }
                    catch { }
                }
            });

            baseDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(baseDir);
            studioDir = Path.Combine(baseDir, "studio");
            string desktopApp = Path.Combine(studioDir, "desktop_app.py");

            if (!File.Exists(desktopApp))
            {
                MessageBox.Show(
                    "Không tìm thấy thư mục ứng dụng tại:\n" + desktopApp + "\n\nVui lòng giải nén đầy đủ tất cả các tệp.",
                    AppTitle,
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
                return;
            }

            string portablePython = Path.Combine(studioDir, "runtime", "python", "python.exe");
            string portablePythonw = Path.Combine(studioDir, "runtime", "python", "pythonw.exe");
            string venvDir = Path.Combine(studioDir, ".venv");
            string pythonExe = File.Exists(portablePython) ? portablePython : Path.Combine(venvDir, "Scripts", "python.exe");
            string pythonwExe = File.Exists(portablePythonw) ? portablePythonw : (File.Exists(portablePython) ? portablePython : Path.Combine(venvDir, "Scripts", "pythonw.exe"));

            // 1. First-time setup check (Only triggered if neither portable Python nor .venv exists)
            if (!File.Exists(pythonExe))
            {
                using (var setupForm = new SetupForm(baseDir, studioDir))
                {
                    DialogResult res = setupForm.ShowDialog();
                    if (res != DialogResult.OK || !File.Exists(pythonExe))
                    {
                        return;
                    }
                }
            }

            // 2. Launch the one backend and supervise it independently from Edge.
            string targetPython = File.Exists(pythonwExe) ? pythonwExe : pythonExe;
            try { StartBackend(targetPython, desktopApp); }
            catch (Exception ex)
            {
                MessageBox.Show("Không khởi động được máy chủ Studio:\n" + ex.Message,
                    AppTitle, MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            // 3. Tray + watchdog. Chromium may hand off --app to another
            // process and exit instantly; never treat that as Studio shutdown.
            SetupTray();
            backendTimer = new System.Threading.Timer(
                delegate(object state) { SuperviseBackend(targetPython, desktopApp); },
                null, TimeSpan.FromSeconds(5), TimeSpan.FromSeconds(8));
            Application.Run();
        }

        private static void StartBackend(string python, string desktopApp)
        {
            var psi = new ProcessStartInfo
            {
                FileName = python,
                Arguments = "\"" + desktopApp + "\"",
                WorkingDirectory = baseDir,
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden
            };
            // The EXE, not Python's transient Edge child PID, owns the one UI.
            psi.EnvironmentVariables["STORYBOARD_NATIVE_WINDOW_OWNER"] = "1";
            pythonProcess = Process.Start(psi);
            if (pythonProcess == null) throw new InvalidOperationException("Backend process missing.");
        }

        private static bool BackendHealthy()
        {
            try
            {
                var req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:8765/api/status");
                req.Timeout = 1400;
                req.ReadWriteTimeout = 1400;
                req.Proxy = null;
                using (var response = (HttpWebResponse)req.GetResponse())
                    return response.StatusCode == HttpStatusCode.OK;
            }
            catch { return false; }
        }

        private static void SuperviseBackend(string python, string desktopApp)
        {
            if (shuttingDown) return;
            if (!Monitor.TryEnter(backendLock)) return;
            try
            {
                if (shuttingDown) return;
                if (BackendHealthy())
                {
                    if (!uiPresented)
                    {
                        uiPresented = true;
                        OpenStudioWindow();
                    }
                    return;
                }
                // A slow import/Flow login must not trigger duplicate Python.
                if (pythonProcess != null && !pythonProcess.HasExited) return;
                if ((DateTime.UtcNow - restartWindow).TotalMinutes > 10)
                {
                    restartWindow = DateTime.UtcNow;
                    backendFailures = 0;
                }
                if (++backendFailures > 4)
                {
                    if (trayIcon != null) trayIcon.Text = "Storyboard AI - cần kiểm tra máy chủ";
                    return;
                }
                StartBackend(python, desktopApp);
                if (trayIcon != null) trayIcon.Text = "Storyboard AI - đang khôi phục máy chủ";
            }
            catch { }
            finally { Monitor.Exit(backendLock); }
        }

        private static bool RestoreExistingStudioWindow()
        {
            bool found = false;
            EnumWindows(delegate(IntPtr hwnd, IntPtr ignored) {
                if (!IsWindowVisible(hwnd)) return true;
                var sb = new System.Text.StringBuilder(256);
                GetWindowText(hwnd, sb, sb.Capacity);
                string title = sb.ToString();
                if (title.IndexOf("Storyboard AI", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    ShowWindow(hwnd, 9);
                    SetForegroundWindow(hwnd);
                    found = true;
                    return false;
                }
                return true;
            }, IntPtr.Zero);
            return found;
        }

        private static void SetupTray()
        {
            try
            {
                Icon appIcon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
                trayIcon = new NotifyIcon();
                trayIcon.Icon = appIcon ?? SystemIcons.Application;
                trayIcon.Text = "Storyboard AI Studio Pro (Đang chạy)";
                trayIcon.Visible = true;

                var menu = new ContextMenuStrip();
                var itemOpen = new ToolStripMenuItem("🎬 Mở Cửa Sổ Studio");
                itemOpen.Font = new Font(itemOpen.Font, FontStyle.Bold);
                itemOpen.Click += (s, e) => { OpenStudioWindow(); };
                menu.Items.Add(itemOpen);

                var itemProds = new ToolStripMenuItem("📁 Mở Thư Mục Video (Productions)");
                itemProds.Click += (s, e) =>
                {
                    string prodDir = Path.Combine(studioDir, "productions");
                    Directory.CreateDirectory(prodDir);
                    Process.Start("explorer.exe", prodDir);
                };
                menu.Items.Add(itemProds);

                menu.Items.Add(new ToolStripSeparator());

                var itemExit = new ToolStripMenuItem("❌ Thoát Phần Mềm");
                itemExit.Click += (s, e) => { ExitApplication(); };
                menu.Items.Add(itemExit);

                trayIcon.ContextMenuStrip = menu;
                trayIcon.DoubleClick += (s, e) => { OpenStudioWindow(); };

                trayIcon.ShowBalloonTip(
                    2500,
                    "Storyboard AI Studio Pro",
                    "Phần mềm đã khởi động thành công! Bạn có thể nhấp vào biểu tượng này để mở lại giao diện bất kỳ lúc nào.",
                    ToolTipIcon.Info);
            }
            catch { }
        }

        private static void OpenStudioWindow()
        {
            if (!BackendHealthy()) return;
            if (RestoreExistingStudioWindow()) { uiPresented = true; return; }
            string url = "http://127.0.0.1:8765";
            string uiProfile = Path.Combine(studioDir, "runtime", ".desktop_ui_profile");
            try { Directory.CreateDirectory(uiProfile); } catch { }
            string[] browsers = new string[]
            {
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                Environment.ExpandEnvironmentVariables(@"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
                Environment.ExpandEnvironmentVariables(@"%LocalAppData%\Microsoft\Edge\Application\msedge.exe")
            };

            foreach (var b in browsers)
            {
                if (File.Exists(b))
                {
                    try
                    {
                        string args = "--app=" + url + " --user-data-dir=\"" + uiProfile + "\" --window-size=1400,850 --window-position=50,30 --no-first-run --no-default-browser-check --disable-features=msHub,msEdgeAppModeAddressBar --app-id=StoryboardAIStudioPro";
                        Process.Start(b, args);
                        return;
                    }
                    catch { }
                }
            }

            // Do not launch an unrelated default web browser as fallback.
            if (trayIcon != null)
                trayIcon.ShowBalloonTip(2500,"Storyboard AI",
                    "Không tìm thấy trình duyệt chạy ở chế độ ứng dụng.",
                    ToolTipIcon.Warning);
        }

        private static void ExitApplication()
        {
            shuttingDown = true;
            if (backendTimer != null) backendTimer.Dispose();

            if (trayIcon != null)
            {
                trayIcon.Visible = false;
                trayIcon.Dispose();
            }

            // Cleanup python desktop app and server
            try
            {
                if (pythonProcess != null && !pythonProcess.HasExited)
                {
                    pythonProcess.Kill();
                }
            }
            catch { }

            // Cleanup any process on port 8765
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = "-NoProfile -Command \"Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }\"",
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using (var p = Process.Start(psi))
                {
                    p.WaitForExit(3000);
                }
            }
            catch { }

            Application.Exit();
            Environment.Exit(0);
        }
    }

    public class SetupForm : Form
    {
        private Label lblStatus;
        private ProgressBar progressBar;
        private string baseDir;
        private string studioDir;

        public SetupForm(string baseDir, string studioDir)
        {
            this.baseDir = baseDir;
            this.studioDir = studioDir;

            this.Text = "Storyboard AI Studio Pro - Khởi Tạo Môi Trường";
            this.Width = 520;
            this.Height = 220;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = true;
            this.BackColor = Color.FromArgb(24, 24, 27);
            this.ForeColor = Color.White;

            var title = new Label
            {
                Text = "🎬 STORYBOARD AI STUDIO PRO",
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Color.FromArgb(56, 189, 248),
                Location = new Point(25, 20),
                AutoSize = true
            };
            this.Controls.Add(title);

            lblStatus = new Label
            {
                Text = "Đang kiểm tra môi trường trên máy tính của bạn...",
                Font = new Font("Segoe UI", 9.5f),
                ForeColor = Color.FromArgb(228, 228, 231),
                Location = new Point(25, 60),
                Size = new Size(450, 45)
            };
            this.Controls.Add(lblStatus);

            progressBar = new ProgressBar
            {
                Style = ProgressBarStyle.Marquee,
                MarqueeAnimationSpeed = 30,
                Location = new Point(25, 115),
                Size = new Size(450, 22)
            };
            this.Controls.Add(progressBar);

            this.Shown += SetupForm_Shown;
        }

        private void SetupForm_Shown(object sender, EventArgs e)
        {
            Thread worker = new Thread(DoSetupWork);
            worker.IsBackground = true;
            worker.Start();
        }

        private void UpdateStatus(string message)
        {
            if (this.InvokeRequired)
            {
                this.BeginInvoke(new Action<string>(UpdateStatus), message);
                return;
            }
            lblStatus.Text = message;
        }

        private string FindSystemPython()
        {
            try
            {
                var pCheck = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = "--version",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };
                using (var proc = Process.Start(pCheck))
                {
                    proc.WaitForExit(4000);
                    if (proc.ExitCode == 0) return "python";
                }
            }
            catch { }

            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string progFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);

            string[] candidates = new string[]
            {
                Path.Combine(localApp, @"Programs\Python\Python313\python.exe"),
                Path.Combine(localApp, @"Programs\Python\Python312\python.exe"),
                Path.Combine(localApp, @"Programs\Python\Python311\python.exe"),
                Path.Combine(localApp, @"Programs\Python\Python310\python.exe"),
                Path.Combine(progFiles, @"Python313\python.exe"),
                Path.Combine(progFiles, @"Python312\python.exe"),
                Path.Combine(progFiles, @"Python311\python.exe"),
                Path.Combine(progFiles, @"Python310\python.exe"),
                @"C:\Python312\python.exe",
                @"C:\Python311\python.exe",
                @"C:\Python310\python.exe",
                Path.Combine(localApp, @"Python\pythoncore-3.14-64\python.exe")
            };

            foreach (var cand in candidates)
            {
                if (File.Exists(cand)) return cand;
            }

            return null;
        }

        private void DoSetupWork()
        {
            try
            {
                UpdateStatus("Bước 1/3: Kiểm tra Python trên hệ thống...");
                Thread.Sleep(500);

                string sysPython = FindSystemPython();

                if (string.IsNullOrEmpty(sysPython))
                {
                    bool autoInstall = false;
                    this.Invoke(new Action(() =>
                    {
                        DialogResult d = MessageBox.Show(
                            "Máy tính của bạn chưa cài đặt Python!\n\n" +
                            "Bạn có muốn phần mềm TỰ ĐỘNG tải và cài đặt Python 3.11 chính thức (1-Click Tự Động 100%) không?\n\n" +
                            "- Chọn [Yes]: Tự động cài đặt nhanh chóng (Khuyên dùng)\n" +
                            "- Chọn [No]: Tôi tự cài đặt thủ công",
                            "Storyboard AI Studio Pro - Cài Đặt Môi Trường",
                            MessageBoxButtons.YesNo,
                            MessageBoxIcon.Question);

                        if (d == DialogResult.Yes)
                        {
                            autoInstall = true;
                        }
                        else
                        {
                            try { Process.Start("https://www.python.org/downloads/"); } catch { }
                            this.DialogResult = DialogResult.Cancel;
                            this.Close();
                        }
                    }));

                    if (!autoInstall) return;

                    UpdateStatus("Đang tự động tải bộ cài Python 3.11 chính thức...");
                    try
                    {
                        ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072;
                        string installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe";
                        string tempInstaller = Path.Combine(Path.GetTempPath(), "python_setup_temp.exe");

                        using (var wc = new WebClient())
                        {
                            wc.DownloadFile(installerUrl, tempInstaller);
                        }

                        UpdateStatus("Đang cài đặt Python 3.11 vào hệ thống...");
                        var pInstall = new ProcessStartInfo
                        {
                            FileName = tempInstaller,
                            Arguments = "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 SimpleInstall=1",
                            UseShellExecute = false,
                            CreateNoWindow = true
                        };
                        using (var proc = Process.Start(pInstall))
                        {
                            proc.WaitForExit(180000);
                        }

                        try { File.Delete(tempInstaller); } catch { }
                    }
                    catch (Exception ex)
                    {
                        throw new Exception("Không thể tự động tải/cài đặt Python: " + ex.Message);
                    }

                    sysPython = FindSystemPython();
                    if (string.IsNullOrEmpty(sysPython))
                    {
                        throw new Exception("Đã cài đặt xong nhưng chưa thể nhận diện Python. Vui lòng thử mở lại phần mềm.");
                    }
                }

                string venvDir = Path.Combine(studioDir, ".venv");
                string pythonExe = Path.Combine(venvDir, "Scripts", "python.exe");

                UpdateStatus("Bước 2/3: Khởi tạo môi trường ảo độc lập (.venv)...");
                var pVenv = new ProcessStartInfo
                {
                    FileName = sysPython,
                    Arguments = "-m venv \"" + venvDir + "\"",
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using (var proc = Process.Start(pVenv))
                {
                    proc.WaitForExit(90000);
                    if (proc.ExitCode != 0 || !File.Exists(pythonExe))
                    {
                        throw new Exception("Không thể tạo môi trường ảo .venv.");
                    }
                }

                UpdateStatus("Bước 3/3: Đang tải thư viện AI (khoảng 1 - 2 phút)...");
                string reqFile = Path.Combine(studioDir, "requirements.txt");
                string pipArgs = File.Exists(reqFile)
                    ? "-m pip install -r \"" + reqFile + "\""
                    : "-m pip install requests google-genai gTTS pillow opencv-python-headless numpy edge-tts customtkinter python-dotenv";

                var pPip = new ProcessStartInfo
                {
                    FileName = pythonExe,
                    Arguments = pipArgs,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using (var proc = Process.Start(pPip))
                {
                    proc.WaitForExit(300000);
                    if (proc.ExitCode != 0)
                    {
                        throw new Exception("Quá trình cài đặt thư viện bị lỗi. Vui lòng kiểm tra lại kết nối mạng.");
                    }
                }

                this.Invoke(new Action(() =>
                {
                    this.DialogResult = DialogResult.OK;
                    this.Close();
                }));
            }
            catch (Exception ex)
            {
                this.Invoke(new Action(() =>
                {
                    MessageBox.Show(
                        "Lỗi trong quá trình khởi tạo môi trường:\n" + ex.Message,
                        "Storyboard AI Studio Pro",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);
                    this.DialogResult = DialogResult.Cancel;
                    this.Close();
                }));
            }
        }
    }
}
