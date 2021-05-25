[![Codacy Badge](https://app.codacy.com/project/badge/Grade/495cf6fc5be8434ca7b493ff88724433)](https://www.codacy.com/gh/dream-alpha/MovieCockpit/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=dream-alpha/MovieCockpit&amp;utm_campaign=Badge_Grade)

<a href="https://gemfury.com/f/partner">
  <img src="https://badge.fury.io/fp/gemfury.svg" alt="Public Repository">
</a>

# MovieCockpit (MVC)
## Features
- MVC is a movie list for DreamOS settop boxes
- MVC implements a permanent sqlite movie cache which allows MVC to display the movie list with all its information without disk access. So, no spinners or delays due to disk spinup.
- MVC imports all movies located in the E2 movie directories, which can be located on multiple physical disks.
- MVC implements exact event start time and duration rather than recording start time and duration which includes margins before and after the event as implemented in the standard DreamOS.
- MVC provides 5 predefined list styles which can be modified easily.
- MVC provides a smart jump function that conventiently allows to skip advertisements using the bouquet keys by adapting the skip distance automatically.
- MVC provides a manual/automatic backup function that allows to record movies to an internal disk and then move it to external backup media (USB/NAS)
- MVC implements an auto-mount manager that dynamically recognizes and mounts network drives powering on/off

## Limitations
- MVC supports DreamOS only
- MVC is being tested on DM 920 and DM ONE only
- MVC supports FHD (Full HD) skins only

## Installation
To install MovieCockpit execute the following command in a console on your dreambox:
- apt-get install wget (only required the first time)
- wget https://dream-alpha.github.io/MovieCockpit/moviecockpit.sh -O - | /bin/sh

The installation script will also install a feed source that enables a convenient upgrade to the latest version with the following commands or automatically as part of a DreamOS upgrade:
- apt-get update
- apt-get upgrade

## Links
- Support thread: https://dreambox.de/board/index.php?thread/23864-moviecockpit/
- Package feed: https://gemfury.com/dream-alpha
