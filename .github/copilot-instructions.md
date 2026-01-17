# Copilot Instructions for MicroservicesLab-IdentityService

## General Guidelines
- Always use the latest stable versions of packages and libraries
- Follow industry best practices and coding standards
- Include comprehensive type hints and proper documentation
- Prioritize code readability and maintainability
- Write clean, DRY (Don't Repeat Yourself) code

## Python-Specific
- Use Python 3.12+ features when appropriate
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Include docstrings for classes and functions

## Project-Specific Technologies
- Use SQLAlchemy 2.x syntax with Mapped types and mapped_column
- Assume it is used MS SQL 2022 unless it is specifically mentioned
- Follow FastAPI best practices for API development
- Use UUID (uuid.UUID) for primary keys consistently
- Implement proper error handling with custom exceptions
- Use Pydantic v2 for data validation and serialization
- Follow async/await patterns for database operations

## Security
- Never hardcode credentials or sensitive data
- Use environment variables for configuration
- Implement proper authentication and authorization
- Hash passwords using secure algorithms (bcrypt, argon2)
- Validate and sanitize all user inputs

## Database
- Use migrations for schema changes (Alembic)
- Include proper indexes on foreign keys and frequently queried fields
- Use UTC for all datetime operations
- Implement soft deletes where appropriate