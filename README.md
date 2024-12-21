<h1>Chat Psychologist AI</h1>

## macOS/Linux
### Installation

-   Clone this repository
    ```bash
    git clone git@github.com:appdevorangesellers/ChatPsychologistAI.git ChatPsychologistAI
    ```
-   Move to the root project
    ```bash
    cd ChatPsychologistAI
    ```
-   Create .env file (Drive: Chat Psychologist > 4. Training > Chat App > env_file_explanation.mov)
    ```bash
    # ask for keys in the project channel
    cp application/.env.example application/.env
    ```
-   Create databaseKey.json file (Drive: Chat Psychologist > 4. Training > Chat App > databaseKey.json_file_explanation.mov)
    ```bash
    # ask for the content of the file in project channel
    cp application/databaseKey.json.example application/databaseKey.json
    ```
-   Create a virtual environment
    ```bash
    python3 -m venv .venv
    ```
-   Activate the virtual environment
    ```bash
    . .venv/bin/activate
    ```
-   Update pip (Optional)
    ```bash
    pip install --upgrade pip
    ```
-   Install pip-tools, pip-chill
    ```bash
    pip install pip-tools pip-chill
    ```
-   Install depedencies
    ```bash
    # List of packages and plugins:
    # Drive: Chat Psychologist > 4. Training > Chat App > Packages_and_Plugins.docx)
    pip-sync
    ```

### Run the application

-   (If the virtual environment is not activated) Activate the virtual environment
    ```bash
    . .venv/bin/activate
    ```
-   Update depedencies (Optional)
    ```bash
    pip-sync
    ```
-   Run the application
    ```bash
    flask --app application/appreg run
    ```


### When you add new packages

When you add new packages to the project, `requirements.in` and `requirements.txt` files should be updated.

-   Update minimal set of packages
    ```bash
    pip-chill > requirements.in
    ```
-   Compile complete list of required packages
    ```bash
    pip-compile requirements.in
    ```

Template URL: https://bootstrapmade.com/restaurantly-restaurant-template/
Author: Tanja Grozdani



