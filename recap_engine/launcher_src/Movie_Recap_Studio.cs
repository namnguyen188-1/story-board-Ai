using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace MovieRecapStudio
{
    static class Program
    {
        private static readonly string AppTitle = "Movie Recap Studio Pro v0.0.1";
        private static Mutex singleInstanceMutex = null;
        private static Process pythonProcess = null;

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int GetWindowText(IntPtr hwnd, System.Text.StringBuilder text, int max);
        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hwnd);
        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hwnd, int nCmdShow);
        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")]
        private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
        private delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr lParam);

        private static void Log(string msg)
        {
            try
            {
                string logFile = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "recap_launcher.log");
                File.AppendAllText(logFile, string.Format("[{0:yyyy-MM-dd HH:mm:ss}] {1}\r\n", DateTime.Now, msg));
            }
            catch { }
        }

        [STAThread]
        static void Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Log("=== Movie Recap Studio Launcher Started ===");

            bool isNewInstance;
            singleInstanceMutex = new Mutex(true, "MovieRecapStudioPro_Qt6_SingleInstance_2026", out isNewInstance);
            Log("Mutex check: isNewInstance = " + isNewInstance);
            if (!isNewInstance)
            {
                // If already running and visible, bring existing Qt6 window to foreground
                if (RestoreExistingStudioWindow())
                {
                    Log("Restored existing studio window successfully. Exiting launcher.");
                    return;
                }
                Log("Existing window not found, continuing with new instance.");
            }

            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(baseDir);
            Log("BaseDir: " + baseDir);

            // 1. Locate recap_engine directory
            string recapDir = baseDir;
            if (Directory.Exists(Path.Combine(baseDir, "recap_engine")))
            {
                recapDir = Path.Combine(baseDir, "recap_engine");
            }
            else if (File.Exists(Path.Combine(baseDir, "qt6_app.py")))
            {
                recapDir = baseDir;
            }
            else if (Directory.Exists(@"D:\STORYBOARD_AI\recap_engine"))
            {
                recapDir = @"D:\STORYBOARD_AI\recap_engine";
            }
            Log("RecapDir resolved to: " + recapDir);

            // 1. Ensure backend server is running on port 8095
            bool serverReady = false;
            try
            {
                var req = (System.Net.HttpWebRequest)System.Net.WebRequest.Create("http://127.0.0.1:8095/api/status");
                req.Timeout = 800;
                using (var resp = (System.Net.HttpWebResponse)req.GetResponse())
                {
                    if (resp.StatusCode == System.Net.HttpStatusCode.OK) serverReady = true;
                }
            }
            catch { }

            if (!serverReady)
            {
                Log("Starting backend server.py...");
                string serverScript = Path.Combine(baseDir, "server.py");
                string pythonExe = Path.Combine(baseDir, "runtime", "python", "python.exe");
                if (!File.Exists(pythonExe)) pythonExe = "python.exe";

                var serverPsi = new ProcessStartInfo
                {
                    FileName = pythonExe,
                    Arguments = "-u \"" + serverScript + "\"",
                    WorkingDirectory = baseDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Hidden
                };
                Process.Start(serverPsi);
                Thread.Sleep(1200);
            }

            // 2. Launch visible Desktop App window (Edge / Chrome / Default Browser)
            string[] browsers = new string[]
            {
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                Environment.ExpandEnvironmentVariables(@"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")
            };

            string chosenBrowser = null;
            foreach (var b in browsers)
            {
                if (File.Exists(b))
                {
                    chosenBrowser = b;
                    break;
                }
            }

            try
            {
                if (chosenBrowser != null)
                {
                    Log("Launching native app mode via: " + chosenBrowser);
                    var appPsi = new ProcessStartInfo
                    {
                        FileName = chosenBrowser,
                        Arguments = "--app=http://127.0.0.1:8095 --start-maximized --no-first-run --no-default-browser-check",
                        UseShellExecute = true
                    };
                    Process.Start(appPsi);

                    // Ensure window is fully maximized on desktop
                    new Thread(delegate ()
                    {
                        for (int i = 0; i < 40; i++)
                        {
                            Thread.Sleep(250);
                            if (MaximizeStudioWindow()) break;
                        }
                    }).Start();
                }
                else
                {
                    Log("Launching default browser...");
                    Process.Start(new ProcessStartInfo("http://127.0.0.1:8095") { UseShellExecute = true });
                }
            }
            catch (Exception ex)
            {
                Log("EXCEPTION launching browser: " + ex.ToString());
                Process.Start(new ProcessStartInfo("http://127.0.0.1:8095") { UseShellExecute = true });
            }
            Log("=== Movie Recap Studio Launcher Finished ===");
        }

        private static bool MaximizeStudioWindow()
        {
            bool found = false;
            EnumWindows(delegate (IntPtr hwnd, IntPtr ignored)
            {
                if (!IsWindowVisible(hwnd)) return true;
                var sb = new System.Text.StringBuilder(256);
                GetWindowText(hwnd, sb, sb.Capacity);
                string title = sb.ToString();
                if (title.IndexOf("Movie Recap Studio", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    title.IndexOf("Phim Review", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    title.IndexOf("127.0.0.1:8095", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    title.IndexOf("localhost:8095", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    ShowWindow(hwnd, 3); // SW_MAXIMIZE
                    SetForegroundWindow(hwnd);
                    found = true;
                    return false;
                }
                return true;
            }, IntPtr.Zero);
            return found;
        }

        private static bool RestoreExistingStudioWindow()
        {
            bool found = false;
            EnumWindows(delegate (IntPtr hwnd, IntPtr ignored)
            {
                if (!IsWindowVisible(hwnd)) return true;
                var sb = new System.Text.StringBuilder(256);
                GetWindowText(hwnd, sb, sb.Capacity);
                string title = sb.ToString();
                if (title.IndexOf("Movie Recap Studio", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    title.IndexOf("Phim Review", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    title.IndexOf("127.0.0.1:8095", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    title.IndexOf("localhost:8095", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    ShowWindow(hwnd, 3); // SW_MAXIMIZE
                    SetForegroundWindow(hwnd);
                    found = true;
                    return false;
                }
                return true;
            }, IntPtr.Zero);
            return found;
        }
    }
}
