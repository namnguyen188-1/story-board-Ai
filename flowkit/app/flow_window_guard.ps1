param([string]$BrowserProfile,[switch]$Unlock)
$ErrorActionPreference='Stop'
$dir=Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) "state\flow_window"; New-Item $dir -ItemType Directory -Force | Out-Null
$flag=Join-Path $dir 'unlock.flag'
$pidFile=Join-Path $dir 'guard.pid'
if($Unlock){Set-Content -Encoding ascii $flag 'unlock';exit}
# The unlock flag is an explicit user choice. A subsequent job must not clear it.
if(Test-Path $pidFile){
 try{$old=[int](Get-Content $pidFile -Raw);$p=Get-CimInstance Win32_Process -Filter ("ProcessId="+$old)
 if($p -and $p.CommandLine -like '*flow_window_guard.ps1*'){exit}}catch{}
}
Set-Content -Encoding ascii $pidFile $PID
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class LockedFlowWindow {public IntPtr H; public uint P; public string T; public bool Visible;}
public static class LockedFlowNative {
 private delegate bool CB(IntPtr h,IntPtr l);
 [StructLayout(LayoutKind.Sequential)] public struct RECT {public int L,T,R,B;}
 [DllImport("user32.dll")] private static extern bool EnumWindows(CB cb,IntPtr l);
 [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] private static extern int GetWindowText(IntPtr h,StringBuilder t,int n);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] private static extern int GetClassName(IntPtr h,StringBuilder c,int n);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
 [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
 [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h,IntPtr z,int x,int y,int w,int he,uint f);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
 public static List<LockedFlowWindow> Windows(){
 var a=new List<LockedFlowWindow>();CB cb=(h,l)=>{uint p;GetWindowThreadProcessId(h,out p);var t=new StringBuilder(512);var c=new StringBuilder(256);GetWindowText(h,t,512);GetClassName(h,c,256);
 if(c.ToString()=="Chrome_WidgetWin_1" && t.Length>0)a.Add(new LockedFlowWindow{H=h,P=p,T=t.ToString(),Visible=IsWindowVisible(h)});
 return true;};EnumWindows(cb,IntPtr.Zero);GC.KeepAlive(cb);return a;}
}
"@
try {
    $cWnd = [LockedFlowNative]::GetConsoleWindow()
    if ($cWnd -ne [IntPtr]::Zero) { [LockedFlowNative]::ShowWindow($cWnd, 0) }
} catch {}
$script:browserIds=@()
$script:lastBrowserRestart=[DateTime]::Now
$script:flowRoot=Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$script:browserPython=Join-Path $script:flowRoot 'engines\muse\runtime\muse\python\pythonw.exe'
$script:browserLauncher=Join-Path $script:flowRoot 'app\flow_browser.py'
$script:nextRefresh=[DateTime]::MinValue
$script:unlocked=$false
$script:known=@{}
$script:busy=$false
function Update-FlowLock {
 if($script:busy){return}
 $script:busy=$true
 try{
  if([DateTime]::Now -ge $script:nextRefresh){
   $script:browserIds=@(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($BrowserProfile) -and $_.CommandLine -notmatch '--type=' } | ForEach-Object {[uint32]$_.ProcessId})
   $script:nextRefresh=[DateTime]::Now.AddSeconds(5)
   # Only restart this kit's Chrome profile when its browser process is absent.
   # No job submission or changes to other Chrome profiles.
   $cfgFile=Join-Path $script:flowRoot 'settings.json'
   $mode='on_demand'
   try{if(Test-Path $cfgFile){$mode=(Get-Content $cfgFile -Raw|ConvertFrom-Json).browser_mode}}catch{}
   if($mode -ne 'on_demand' -and $script:browserIds.Count -eq 0 -and ([DateTime]::Now-$script:lastBrowserRestart).TotalSeconds -ge 15){
    $script:lastBrowserRestart=[DateTime]::Now
    if((Test-Path $script:browserPython) -and (Test-Path $script:browserLauncher)){
     Start-Process -FilePath $script:browserPython -ArgumentList @('-B','-u',('"'+$script:browserLauncher+'"')) -WindowStyle Hidden
    }
   }
  }
  $show=Test-Path $flag
  $wins=@([LockedFlowNative]::Windows() | Where-Object {$script:browserIds -contains $_.P})
  foreach($w in $wins){
   $key=$w.H.ToInt64().ToString()
   if($show){
    if(-not $script:unlocked){
     $null=[LockedFlowNative]::ShowWindow($w.H,9)
     $null=[LockedFlowNative]::SetWindowPos($w.H,[IntPtr]::Zero,80,80,1000,700,0x14)
    }
   } else {
    $r=New-Object LockedFlowNative+RECT
    $null=[LockedFlowNative]::GetWindowRect($w.H,[ref]$r)
    if(-not $script:known.ContainsKey($key) -or $w.Visible -or $r.L -gt -20000){
     $null=[LockedFlowNative]::SetWindowPos($w.H,[IntPtr]::Zero,-32000,-32000,1100,800,0x14)
     $null=[LockedFlowNative]::ShowWindow($w.H,0)
     $script:known[$key]=$true
    }
   }
  }
  $script:unlocked=$show
  $tray.Text=if($show){'FlowKit - cua so da mo khoa'}else{'FlowKit - cua so dang khoa an'}
 }catch{($_.Exception.Message) | Add-Content (Join-Path $dir 'guard_errors.log')}
 finally{$script:busy=$false}
}
$tray=New-Object System.Windows.Forms.NotifyIcon
$tray.Icon=[System.Drawing.SystemIcons]::Application
$tray.Text='FlowKit - khoa an'
$menu=New-Object System.Windows.Forms.ContextMenuStrip
$open=$menu.Items.Add('Mo Flow dang nhap')
$open.add_Click({Set-Content -Encoding ascii $flag 'unlock';Update-FlowLock})
$lock=$menu.Items.Add('Khoa an Flow')
$lock.add_Click({Remove-Item $flag -Force -ErrorAction SilentlyContinue;Update-FlowLock})
$tray.ContextMenuStrip=$menu
$tray.Visible=$true
$timer=New-Object System.Windows.Forms.Timer
$timer.Interval=250
$timer.add_Tick({Update-FlowLock})
$timer.Start()
Update-FlowLock
try{[System.Windows.Forms.Application]::Run()}
finally{$timer.Stop();$tray.Visible=$false;$tray.Dispose();Remove-Item $pidFile -Force -ErrorAction SilentlyContinue}
