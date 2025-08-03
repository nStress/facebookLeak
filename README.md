# Person Search Application

This is a Python application with a graphical user interface (GUI) built using `tkinter` for searching and filtering personal data stored in the 2019 Facebook leak. It is designed to efficiently handle large data sets by loading all data into memory and using indexes for fast searches.

## Features

- **Data Loading:** Load data from a specified directory containing `.txt` files.
- **Efficient Search:** Quickly search for records by phone number, user ID, email, city, or name.
- **Advanced Filtering:** Refine search results with multiple criteria, including age range, city, phone number partial matches, and gender.
- **GUI Interface:** A user-friendly interface with a table view to display search results.
- **Data Export:** Export filtered results to a text file or CSV format.
- **Multi-encoding Support:** The application attempts to read files with several common encodings to prevent errors.

## Screenshots


## Leak Download

[Can you download  there](magnet:?xt=urn:btih:0595273ab674e05131a757f69f494a4285b429aa&dn=Facebook%20Leak%20%5b2019%5d%5b533M%20Records%5d%5b106%20Countries%5d)

**Search Results**
![Search Results](https://i.imgur.com/K8NN04L.png)

## Installation

### Prerequisites

- Python 3.6 or higher

### Dependencies

This application uses only standard Python libraries. No external packages are required to be installed with `pip`.

If `tkinter` is not available on your system, you may need to install it. The command for this depends on your operating system:

**On Debian/Ubuntu:**
```bash
sudo apt-get install python3-tk