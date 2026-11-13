@echo off
if exist "D:\MOVIE_RECAP_STUDIO\KHOI_DONG.bat" (
    cd /d "D:\MOVIE_RECAP_STUDIO"
    start "" "KHOI_DONG.bat"
    exit /b
)
if exist "Movie_Recap_Studio.exe" (
    start "" "Movie_Recap_Studio.exe"
    exit /b
)
exit /b