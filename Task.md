Your task is to make the following changes in the project:

*   Currently, the whole project including the CLI and the sending application are both written in Python.
*   The aim is to port the CLI to TypeScript so that the CLI is better managed since TypeScript has better support for TUIs.
*   To improve the UI of the project, implement statefulness, dynamic resizing, scrolling, and making sure that all the content is visible on screen regardless of screen size.
*   Make functionality working by changing the Python project to an email system to a Python API with the same code as written but exposed through an API internally to the TUI.
*   Use some authentication token between the TUI and Python API so that it is secure as well.
*   Make a start command as well so that when the start command is run, the Python API is started in one thread and the TUI is started in another.
*   Make sure that all config changes are still handled by Python API and TypeScript interface TUIs just a TypeScript interface.
*   Allow the user to have different configurations and save them so that they can change between them.
*   These configurations should include all the configurable details which are currently there in the TUI.
*   You may use FastAPI to provision the internal API so that it is lightweight. (use FastAPI instead of flask since it is more efficient and has better support for async operations which will be beneficial for our use case).
*   Make sure that the program remains lightweight and easy to run, and everything is working in a proper manner.


Use the tools and skills provided to you along with To-Do's, sequentialthinking and context7 to implement everything in a best possible and most efficient way.


For python, use uv and use bun for typescript. 
Update the readme file to reflect the changes made in the project and provide instructions on how to run the project with the new architecture.
