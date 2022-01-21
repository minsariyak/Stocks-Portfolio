# stocks-portfolio
A flask web application that allows users to manage (buy/sell) stocks. It integrates the IEX API to query actual stock values. 

### How to run the application
1. Download this repository as a zip file and extract the contents.
2. Open a command prompt terminal and change directory to the folder extracted in the step above. 
3. Type the following command:

    > flask run
4. Copy the link generated and type it into a web browser. The link is displayed at the last line that looks like the following:

    > INFO:  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

### Application Strcuture & explanation of files/folders
- **/static:** all static data such as CSS files, JavaScript files, and images are stored in this folder as per Flask standards. 
- **/templates:** all HTML files of the application are stored in this folder as per Flask standards.
- **app.py:** a python file defining the backend logic of the application.
- **helpers.py:** a python file defining functions that are used in "app.py" to simplify code readability.
- **finance.db:** a SQLite database file which stores in various tables; registered users credentials, their purchased stocks, and a history of the interaction with each stock. 
- **requirements.txt:** a plain text file stating all dependencies of the application.

### Screenshots of the application
##### The Index Page - Lists all stocks owned by user
![Index Page Display Error](/readme_imgs/index.png)
##### The Quote Page - Shows the value of a certain stock
![Quote Page Display Error](/readme_imgs/quote.png)
##### The History Page - Shows history of all transactions
![History Page Display Error](/readme_imgs/history.png)
