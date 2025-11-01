@echo off
echo Creating fresh branch without history...
git checkout --orphan fresh-main
git add -A
git commit -m "Initial commit - UMUHUZA Project"
git branch -D main
git branch -m main
git push -f origin main
echo Done! Project pushed successfully.
pause

