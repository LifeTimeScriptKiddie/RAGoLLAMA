#!/bin/bash

# RattGoLLAMA User Management Script
# Adds users to the PostgreSQL database for Streamlit authentication

set -e

echo "🦙 RattGoLLAMA User Management"
echo "============================="

# Load env vars (if present) for DB creds
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

# Defaults if env not set
: "${POSTGRES_USER:=rattg_user}"
: "${POSTGRES_PASSWORD:=changeme}"
: "${POSTGRES_DB:=rattgllm}"

# Check if containers are running
if ! docker compose ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL container is not running"
    echo "Please start the system first: docker compose up -d"
    exit 1
fi

# Function to add user
add_user() {
    local username=$1
    local password=$2
    local role=$3
    
    echo "Adding user: $username with role: $role"
    
    # Generate password hash using passlib inside the API container (has deps)
    if ! docker compose ps ingestion-api | grep -q "Up"; then
        echo "❌ ingestion-api container is not running (needed to hash passwords)"
        echo "Please start it: docker compose up -d ingestion-api"
        exit 1
    fi

    # Use passlib[bcrypt] for a proper bcrypt hash
    password_hash=$(docker compose exec -T -e PASSWORD_INPUT="$password" ingestion-api python - << 'PY'
from passlib.context import CryptContext
import os, sys
pwd = os.environ.get('PASSWORD_INPUT')
if not pwd:
    sys.exit(1)
ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(ctx.hash(pwd))
PY
    )
    
    if [ -z "$password_hash" ]; then
        echo "❌ Failed to generate password hash"
        exit 1
    fi
    
    # Insert user into database
    docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
INSERT INTO users (username, password_hash, roles, created_at) 
VALUES ('$username', '$password_hash', '$role', NOW())
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    roles = EXCLUDED.roles;
EOF
    
    echo "✅ User '$username' added/updated successfully"
}

# Function to list users
list_users() {
    echo "📋 Current users:"
    docker compose exec -T postgres psql -U rattg_user -d rattgllm -c "
        SELECT id, username, roles, created_at 
        FROM users 
        ORDER BY created_at;
    "
}

# Function to delete user
delete_user() {
    local username=$1
    echo "Deleting user: $username"
    
    docker compose exec -T postgres psql -U rattg_user -d rattgllm -c "
        DELETE FROM users WHERE username = '$username';
    "
    
    echo "✅ User '$username' deleted"
}

# Main menu
case "${1:-}" in
    "add")
        if [ $# -ne 4 ]; then
            echo "Usage: $0 add <username> <password> <role>"
            echo "Roles: admin, user"
            exit 1
        fi
        add_user "$2" "$3" "$4"
        ;;
    "list")
        list_users
        ;;
    "delete")
        if [ $# -ne 2 ]; then
            echo "Usage: $0 delete <username>"
            exit 1
        fi
        delete_user "$2"
        ;;
    *)
        echo "RattGoLLAMA User Management"
        echo ""
        echo "Usage:"
        echo "  $0 add <username> <password> <role>    - Add/update user"
        echo "  $0 list                                - List all users"  
        echo "  $0 delete <username>                   - Delete user"
        echo ""
        echo "Examples:"
        echo "  $0 add john secret123 user"
        echo "  $0 add admin newpass admin"
        echo "  $0 list"
        echo "  $0 delete john"
        echo ""
        echo "Roles: admin, user"
        ;;
esac
