# Calla's personalized pomodoro

Functions:
1. Set time for every round of focus and rest
2. Personalized encouragement:
   * before focus
   * during focus
   * after focus
   * complete focus
3. Rating after focus, and compute effective focus time accordingly
4. During rest: show character's quote; Tagore's poems and suggest activities to have a rest

# Usage
1. Run directly in terminal
```bash
python /path/to/calla_pomodoro.py
```
2. Build `.exe`
```bash
pip install pyinstaller
pyinstaller -F -w -i "fox.ico" /path/to/calla_pomodoro.py
# and copy data.json, fox.ico into ./dist folder
# click exe file in ./dist folder; one can also create a shortcut for convenience
```