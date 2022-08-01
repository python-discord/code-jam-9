**Python Discord Summer Code Jam 2022** submission from the team **KinglyKelpies**
# *for level_id in range(14)*
<p align="center">
    <img src="https://user-images.githubusercontent.com/62175543/182180722-6496cbdc-d033-41fd-ae5c-936ad99b635b.gif">
</p

A simple multiplayer puzzle game, 
in which you aim is to reach the goal by pressing buttons, standing on plates, moving boxes.
Together with a friend!

But some say that a few bugs snuck in...

# Table of contents
1. [Installation](https://github.com/Kingly-elpies/KinglyKelpies/blob/read-me-update/README.md#installation)
2. [How to Run](https://github.com/Kingly-elpies/KinglyKelpies/blob/read-me-update/README.md#how-to-run)
3. [How to join a game](https://github.com/Kingly-elpies/KinglyKelpies/blob/read-me-update/README.md#how-to-join-a-game)
4. [How to play](https://github.com/Kingly-elpies/KinglyKelpies/blob/read-me-update/README.md#how-to-play)


# Installation
### 0. Requirements:
   - access *python 3.10* on you system

### 1. Download:
   Run this command in the directory you want to download it to.
   ```shell
   $ git clone https://github.com/Kingly-elpies/KinglyKelpies
   ```
 
### 2. Create a venv
  with python as python as python 3.10 create a virtual environment in the folder `.venv`.
  ```shell
  $ python -m venv .venv
  ```

  #### Enter the environment
  It will change based on your operating system and shell.
  ```shell
  # Linux, Bash
  $ source .venv/bin/activate
  # Linux, Fish
  $ source .venv/bin/activate.fish
  # Linux, Csh
  $ source .venv/bin/activate.csh
  # Linux, PowerShell Core
  $ .venv/bin/Activate.ps1
  # Windows, cmd.exe
  > .venv\Scripts\activate.bat
  # Windows, PowerShell
  > .venv\Scripts\Activate.ps1
  ```

  #### Exiting the environment 
  Run this after you played our game.
  ```shell
  $ deactivate
  ```

### 3. Install the dependencies
  In the `/KinglyKelpies` directory run:
  ```shell
  $ pip insall -r dev-requirements.txt
  ```
  This installs all modules you need to run the game

#### Now you are setup to run the game!
  
# How to Run
  - First follow or instructions for [Installation](https://github.com/Kingly-elpies/KinglyKelpies/edit/read-me-update/README.md#installation)
  - Then run in the venv:
  ```shell
  $ python main.py
  ```  
  - you will be greeted by our main menu
  
# How To join a game:
From the Main menu
- press on `Host`, if you want to host a game. After that enter the port you want to host the game and press the arrow to the right.
- press on `Client`, if you want to join a game. After that enter the ip of the host and the port to connect to `ip:host`.

# How to play:
### Controlls
   - `w` for up   
   - `a` for left
   - `s` for down  
   - `d` for right
   - `e` to press buttons
   - `q` to pick up boxes and put them down
   - `esc` to open the pause menu
      - the host can acces the level menue from here
      - by hitting reload you can r̵͎̀e̷̪̤̟̠͓̥͑͋̓́͊̀̚ḻ̸̰̯̏̑͛̂̎̄̽͘ơ̶̮̼̯͋̅͛å̴͇͍̩̲̍̈́͘d̶͇̰͐̓͑͒̕ the game
### Objects
<!-- Button-->
<p align="left">
    <img height=48 width=48 align="top" src = "https://user-images.githubusercontent.com/62175543/182188591-da67cfd8-0e70-4a2c-824e-f682fe93278f.gif">
    <t> A button can be toggled beween on or off, used to open and close doors</t>
</p>

<!-- Plate-->
<p align="left">
    <img height=48 width=48 align="top" src = "https://user-images.githubusercontent.com/62175543/182190339-8801967b-7d60-4260-92c6-eddc30f956b4.gif">
    <t> A Plate is toggled on or off if a player walks or a box is placed on it, used to open and close doors</t>
</p>

<!-- Door-->
<p align="left">
    <img height=48 width=48 align="top" src = "https://user-images.githubusercontent.com/62175543/182191249-53668d2d-0eb8-493f-aa8f-8e5399d44468.gif">
    <t> A Door can be opend by plates and buttons. Sometimes more then one of each!</t>
</p>


