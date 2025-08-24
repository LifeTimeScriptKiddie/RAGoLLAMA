#!/bin/bash

# Open WebUI User Management Script
# Manages users in Open WebUI through its API

set -e

OPENWEBUI_URL="http://localhost:3001"

echo "💬 Open WebUI User Management"
echo "=============================="

# Check if Open WebUI is running
if ! curl -s "$OPENWEBUI_URL/health" >/dev/null 2>&1; then
    echo "❌ Open WebUI is not accessible at $OPENWEBUI_URL"
    echo "Please ensure Open WebUI is running: docker compose up -d openwebui"
    exit 1
fi

# Function to create admin user (first user)
create_admin() {
    local name=$1
    local email=$2
    local password=$3
    
    echo "Creating admin user: $name ($email)"
    
    response=$(curl -s -X POST "$OPENWEBUI_URL/api/v1/auths/signup" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"email\": \"$email\",
            \"password\": \"$password\",
            \"role\": \"admin\"
        }")
    
    if echo "$response" | jq -r '.token' >/dev/null 2>&1; then
        echo "✅ Admin user created successfully"
        echo "🔑 Token: $(echo "$response" | jq -r '.token')"
    else
        echo "❌ Failed to create admin user"
        echo "Response: $response"
    fi
}

# Function to get admin token (login)
get_admin_token() {
    local email=$1
    local password=$2
    
    response=$(curl -s -X POST "$OPENWEBUI_URL/api/v1/auths/signin" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$email\",
            \"password\": \"$password\"
        }")
    
    if echo "$response" | jq -r '.token' >/dev/null 2>&1; then
        echo $(echo "$response" | jq -r '.token')
    else
        echo ""
    fi
}

# Function to create regular user
create_user() {
    local admin_token=$1
    local name=$2
    local email=$3
    local password=$4
    local role=${5:-"user"}
    
    echo "Creating user: $name ($email) with role: $role"
    
    response=$(curl -s -X POST "$OPENWEBUI_URL/api/v1/users" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $admin_token" \
        -d "{
            \"name\": \"$name\",
            \"email\": \"$email\",
            \"password\": \"$password\",
            \"role\": \"$role\"
        }")
    
    if echo "$response" | jq -r '.id' >/dev/null 2>&1; then
        echo "✅ User created successfully"
        echo "👤 User ID: $(echo "$response" | jq -r '.id')"
    else
        echo "❌ Failed to create user"
        echo "Response: $response"
    fi
}

# Function to list users
list_users() {
    local admin_token=$1
    
    echo "📋 Open WebUI users:"
    
    response=$(curl -s -X GET "$OPENWEBUI_URL/api/v1/users" \
        -H "Authorization: Bearer $admin_token")
    
    if echo "$response" | jq -r '.[0].id' >/dev/null 2>&1; then
        echo "$response" | jq -r '.[] | "ID: \(.id) | Name: \(.name) | Email: \(.email) | Role: \(.role)"'
    else
        echo "❌ Failed to list users"
        echo "Response: $response"
    fi
}

# Function to delete user
delete_user() {
    local admin_token=$1
    local user_id=$2
    
    echo "Deleting user ID: $user_id"
    
    response=$(curl -s -X DELETE "$OPENWEBUI_URL/api/v1/users/$user_id" \
        -H "Authorization: Bearer $admin_token")
    
    if [ "$response" = "true" ]; then
        echo "✅ User deleted successfully"
    else
        echo "❌ Failed to delete user"
        echo "Response: $response"
    fi
}

# Main menu
case "${1:-}" in
    "init-admin")
        if [ $# -ne 4 ]; then
            echo "Usage: $0 init-admin <name> <email> <password>"
            echo "Example: $0 init-admin \"Admin User\" admin@example.com adminpass123"
            exit 1
        fi
        create_admin "$2" "$3" "$4"
        ;;
    "add")
        if [ $# -lt 5 ]; then
            echo "Usage: $0 add <admin_email> <admin_password> <name> <email> [password] [role]"
            echo "Example: $0 add admin@example.com adminpass123 \"John Doe\" john@example.com userpass123 user"
            exit 1
        fi
        
        admin_token=$(get_admin_token "$2" "$3")
        if [ -z "$admin_token" ]; then
            echo "❌ Failed to authenticate admin user"
            exit 1
        fi
        
        user_password=${6:-"password123"}
        user_role=${7:-"user"}
        create_user "$admin_token" "$4" "$5" "$user_password" "$user_role"
        ;;
    "list")
        if [ $# -ne 3 ]; then
            echo "Usage: $0 list <admin_email> <admin_password>"
            exit 1
        fi
        
        admin_token=$(get_admin_token "$2" "$3")
        if [ -z "$admin_token" ]; then
            echo "❌ Failed to authenticate admin user"
            exit 1
        fi
        
        list_users "$admin_token"
        ;;
    "delete")
        if [ $# -ne 4 ]; then
            echo "Usage: $0 delete <admin_email> <admin_password> <user_id>"
            exit 1
        fi
        
        admin_token=$(get_admin_token "$2" "$3")
        if [ -z "$admin_token" ]; then
            echo "❌ Failed to authenticate admin user"
            exit 1
        fi
        
        delete_user "$admin_token" "$4"
        ;;
    *)
        echo "Open WebUI User Management"
        echo ""
        echo "⚠️  Note: You must create an admin user first through the web interface"
        echo "   or use the init-admin command."
        echo ""
        echo "Usage:"
        echo "  $0 init-admin <name> <email> <password>           - Create first admin user"
        echo "  $0 add <admin_email> <admin_pass> <name> <email> [password] [role] - Add user"
        echo "  $0 list <admin_email> <admin_pass>                - List all users"
        echo "  $0 delete <admin_email> <admin_pass> <user_id>    - Delete user"
        echo ""
        echo "Examples:"
        echo "  $0 init-admin \"Admin User\" admin@rattgollama.com admin123"
        echo "  $0 add admin@rattgollama.com admin123 \"John Doe\" john@company.com"
        echo "  $0 list admin@rattgollama.com admin123"
        echo "  $0 delete admin@rattgollama.com admin123 user-uuid-here"
        echo ""
        echo "💡 Access Open WebUI at: http://localhost:3001"
        ;;
esac