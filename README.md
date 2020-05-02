[![Codacy Badge](https://api.codacy.com/project/badge/Grade/2490fb717d714344bd5a3acf8ff4185e)](https://www.codacy.com/app/swmaniacster/MovieCockpit?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=dream-alpha/MovieCockpit&amp;utm_campaign=Badge_Grade)

<a href="https://gemfury.com/f/partner">
  <img src="https://badge.fury.io/fp/gemfury.svg" alt="Public Repository">
</a>

# MovieCockpit
## MovieCockpit is an Enhanced Movie List for DreamOS Receivers
- MVC implements a permanent sqlite movie cache which allows MVC to display the movie list with all its information without disk access. So, no spinners or delays due to disk spinup.
- MVC imports all movies located in the E2 movie directories, which can be located on multiple physical disks.
- MVC only supports DreamOS
- MVC is being tested on DM920 only
- MVC only supports FHD (Full HD) skins. It will not work on a "HD" skin.

## Installation
To install MovieCockpit execute the following command in a console on your dreambox:
- wget https://dream-alpha.github.io/MovieCockpit/moviecockpit.sh -O - | /bin/sh


The installation script will also install a feed source that enables a convenient upgrade to the latest version with the following commands or automatically as part of a DreamOS upgrade:
- apt-get update
- apt-get upgrade
## MovieCockpit Doxygen
http://moviecockpit.000webhostapp.com/index.html
## MovieCockpit Feed
https://gemfury.com/dream-alpha
