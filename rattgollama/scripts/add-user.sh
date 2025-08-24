#!/bin/bash

# RattGoLLAMA User Management Script
# Adds users to the PostgreSQL database for Streamlit authentication

set -e

echo "🦙 RattGoLLAMA User Management"
echo "============================="

# Check if container is running
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
    
    # Generate password hash using Python
    password_hash=$(docker compose exec -T postgres python3 -c "
import bcrypt
password = '$password'.encode('utf-8')
hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
print(hashed)
" 2>/dev/null || echo "")
    
    # Fallback to simple hash if bcrypt not available
    if [ -z "$password_hash" ]; then
        password_hash="\$2b\$12\$$(echo -n "$password" | openssl dgst -sha256 | cut -d' ' -f2 | head -c 50)"
    fi
    
    # Insert user into database
    docker compose exec -T postgres psql -U rattg_user -d rattgllm << EOF
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