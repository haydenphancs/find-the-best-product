# Find the Best Product

## Description

- Find the Best Product is a Python project designed to help users compare prices across different online markets, focusing on Amazon, Walmart, and eBay (and more).
- The users can pick the best product they want to buy instead of going after each website. It saves time and time is money.
- It’s a Web-based application.
- The project is continuously developed, feel free to contact and dig more into this idea.

## Table of Contents

1. [Installation]
2. [Usage]
3. [Features]
4. [License]
5. [Contact Information]

## Installation

To get started with the project, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/haydenphancs/find-the-best-product.git
    cd find-the-best-product
    ```

2. **Create and activate a virtual environment** (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the required dependencies**:
- Django
- SQlite
- The user can run all of this by running this cmd
  
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up the database**:
    - If you're using Django with SQLite, run the following commands to apply migrations and create the database:
    ```sh
    python manage.py migrate
    ```

## Usage

Here are the basic steps to use the Find the Best Product tool:

1. Run the main script:
    ```sh
    python scraper.py #Mac: python3 scraper.py
    ```
2. Run the database connect to a local website:
    ```sh
    python3 manage.py runserver
    ```

3. View the results and searching:
- Click on the local address (for example: http://127.0.0.1:8000/show/)


## Features

- Automated price comparison across multiple platforms
- Searching for a product
- Supports searching on Amazon, Walmart, eBay (and more)


## License

N/A

## Contact Information

For any questions or feedback, please contact Hayden Phan : haydenphancs@gmail.com
