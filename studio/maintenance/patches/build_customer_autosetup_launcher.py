"""Compile the separate customer setup launcher; do not edit the existing production EXE."""
from pathlib import Path
import subprocess
r=Path(r"D:\STORYBOARD_AI")
stage=r/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
text=(r/"launcher_src"/"Storyboard_AI_Studio.cs").read_text(encoding="utf-8")
a=text.index('            // 1. First-time setup check')
b=text.index('            // 2. Launch the one backend',a)
text=text[:a]+'''            // Bundled portable Python is mandatory. Do not modify Windows system Python.
            if (!File.Exists(portablePython) || !File.Exists(portablePythonw))
            {
                MessageBox.Show("Thiếu Python nhúng. Hãy chạy lại bộ cài Setup để tự sửa.",
                    AppTitle,MessageBoxButtons.OK,MessageBoxIcon.Error);
                return;
            }
            using (var doctor = new CustomerBootstrapWizard(studioDir, portablePython))
            {
                if (doctor.ShowDialog() != DialogResult.OK) return;
            }

'''+text[b:]
a=text.index('            // Cleanup any process on port 8765')
b=text.index('            Application.Exit();',a)
text=text[:a]+'''            // This launcher owns its Python process only. Never terminate a
            // different listening process on the machine's port 8765.
'''+text[b:]
text=text.replace('StoryboardAIStudioPro_SingleInstance_Mutex_2026',
                  'StoryboardAI_Transfer_SingleInstance_Mutex_2026')
text=text.replace('Local\\\\StoryboardAIStudioPro_OpenWindow_2026',
                  'Local\\\\StoryboardAI_Transfer_OpenWindow_2026')
source=stage/"launcher_customer.cs"
source.write_text(text,encoding="utf-8-sig")
compiler=Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")
cmd=[str(compiler),"/nologo","/target:winexe",
     "/win32icon:"+str(stage/"studio"/"web"/"assets"/"storyboard_ai_icon.ico"),
     "/out:"+str(stage/"Storyboard_AI_Studio.exe"),
     "/r:System.Windows.Forms.dll","/r:System.Drawing.dll",
     str(source),str(stage/"customer_setup_wizard.cs")]
result=subprocess.run(cmd,capture_output=True,text=True,timeout=35)
print("CSC_EXIT",result.returncode)
print((result.stdout or result.stderr)[-2200:])
assert result.returncode==0
print("AUTOCHECK_LAUNCHER_BUILD_PASS",flush=True)
