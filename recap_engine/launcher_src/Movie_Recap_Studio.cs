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

        [STAThread]
        static void Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            bool isNewInstance;
            singleInstanceMutex = new Mutex(true, "MovieRecapStudioPro_Qt6_SingleInstance_2026", out isNewInstance);
            if (!isNewInstance)
            {
                // If already running, bring existing Qt6 window to foreground
                RestoreExistingStudioWindow();
                return;
            }

            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(baseDir);

            // 1. Locate recap_engine directory
            string recapDir = baseDir;
            if (File.Exists(Path.Combine(baseDir, "qt6_app.py")))
            {
                recapDir = baseDir;
            }
            else if (Directory.Exists(Path.Combine(baseDir, "recap_engine")))
            {
                recapDir = Path.Combine(baseDir, "recap_engine");
            }
            else if (Directory.Exists(@"D:\STORYBOARD_AI\recap_engine"))
            {
                recapDir = @"D:\STORYBOARD_AI\recap_engine";
            }

            string qtAppScript = Path.Combine(recapDir, "qt6_app.py");
            if (!File.Exists(qtAppScript))
            {
                MessageBox.Show("Không tìm thấy tệp script giao diện Qt6: " + qtAppScript,
                    AppTitle, MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            // 2. Locate Python runtime
            string[] pythonCandidates = new string[]
            {
                Path.Combine(baseDir, "runtime", "python", "pythonw.exe"),
                Path.Combine(baseDir, "runtime", "python", "python.exe"),
                Path.Combine(baseDir, "..", "runtime", "python", "pythonw.exe"),
                Path.Combine(baseDir, "..", "runtime", "python", "python.exe"),
                @"D:\STORYBOARD_AI\studio\runtime\python\pythonw.exe",
                @"D:\STORYBOARD_AI\studio\runtime\python\python.exe",
                Path.Combine(baseDir, "..", "studio", "runtime", "python", "pythonw.exe"),
                Path.Combine(baseDir, "..", "studio", "runtime", "python", "python.exe"),
                Path.Combine(baseDir, ".venv", "Scripts", "pythonw.exe"),
                Path.Combine(baseDir, ".venv", "Scripts", "python.exe"),
                "pythonw.exe",
                "python.exe"
            };

            string pythonExe = "";
            foreach (var p in pythonCandidates)
            {
                if (File.Exists(p))
                {
                    pythonExe = p;
                    break;
                }
            }

            if (string.IsNullOrEmpty(pythonExe))
            {
                pythonExe = "python.exe";
            }

            // 3. Launch native PyQt6 desktop application
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = pythonExe,
                    Arguments = "-u \"" + qtAppScript + "\"",
                    WorkingDirectory = recapDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Hidden
                };

                // Add runtime/ffmpeg to PATH if exists
                string[] ffmpegCandidates = new string[]
                {
                    Path.Combine(baseDir, "runtime", "ffmpeg"),
                    Path.Combine(baseDir, "..", "runtime", "ffmpeg"),
                    Path.Combine(recapDir, "runtime", "ffmpeg")
                };
                foreach (var fdir in ffmpegCandidates)
                {
                    if (Directory.Exists(fdir))
                    {
                        string currentPath = psi.EnvironmentVariables["PATH"] ?? "";
                        psi.EnvironmentVariables["PATH"] = fdir + ";" + currentPath;
                        break;
                    }
                }

                pythonProcess = Process.Start(psi);
                if (pythonProcess != null)
                {
                    pythonProcess.WaitForExit();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Không thể khởi động giao diện Desktop Qt6:\n" + ex.Message,
                    AppTitle, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
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
                if (title.IndexOf("Movie Recap Studio Pro", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    ShowWindow(hwnd, 9); // SW_RESTORE
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
