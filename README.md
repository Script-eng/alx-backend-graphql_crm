# ALX Backend GraphQL CRM

A simple CRM (Customer Relationship Management) backend built with GraphQL and Django.

## Features

- User authentication and authorization
- Manage customers, products, and orders
- Query and mutate data using GraphQL
- Modular and scalable codebase

## Technologies

- Python
- Django
- Graphene-Django (GraphQL)
- Django ORM (with PostgreSQL or SQLite)
- JWT for authentication

## Getting Started

1. **Clone the repository:**
        ```bash
        git clone https://github.com/yourusername/alx-backend-graphql_crm.git
        cd alx-backend-graphql_crm
        ```

2. **Create and activate a virtual environment:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3. **Install dependencies:**
        ```bash
        pip install -r requirements.txt
        ```

4. **Set up environment variables:**
        - Create a `.env` file based on `.env.example`
        - Add your database credentials and JWT secret

5. **Apply migrations:**
        ```bash
        python manage.py migrate
        ```

6. **Start the server:**
        ```bash
        python manage.py runserver
        ```

7. **Access GraphQL Playground:**
        - Visit `http://localhost:8000/graphql/`

## Usage

- Use GraphQL queries and mutations to manage users, customers, products, and orders.
- Refer to the `docs/` folder for example queries and schema details.

## License

This project is licensed under the MIT License.
