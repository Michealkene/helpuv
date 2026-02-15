#!/bin/bash
# OpenClaw Multi-Instance Management Script
# Manages multiple OpenClaw Docker instances

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"

INSTANCES=("instance1" "instance2" "instance3")
COLORS=(
    "\033[0;36m"  # Cyan for instance1
    "\033[0;33m"  # Yellow for instance2
    "\033[0;35m"  # Magenta for instance3
)
NC="\033[0m"  # No Color

function print_header() {
    echo -e "\n${COLORS[$2]}===================================${NC}"
    echo -e "${COLORS[$2]}$1${NC}"
    echo -e "${COLORS[$2]}===================================${NC}\n"
}

function check_env_files() {
    local missing=0
    for i in "${!INSTANCES[@]}"; do
        local instance="${INSTANCES[$i]}"
        if [ ! -f "$DEPLOYMENT_DIR/$instance/.env" ]; then
            echo -e "${COLORS[$i]}⚠️  Missing .env file for $instance${NC}"
            echo "   Copy .env.example to .env and configure your API keys"
            missing=1
        fi
    done
    return $missing
}

function start_all() {
    print_header "🚀 Starting All OpenClaw Instances" 0

    if ! check_env_files; then
        echo -e "\n⚠️  Please create .env files before starting instances"
        return 1
    fi

    for i in "${!INSTANCES[@]}"; do
        local instance="${INSTANCES[$i]}"
        print_header "Starting $instance" $i
        cd "$DEPLOYMENT_DIR/$instance"
        docker-compose up -d
    done

    echo -e "\n✅ All instances started successfully!"
    status_all
}

function stop_all() {
    print_header "🛑 Stopping All OpenClaw Instances" 0

    for i in "${!INSTANCES[@]}"; do
        local instance="${INSTANCES[$i]}"
        print_header "Stopping $instance" $i
        cd "$DEPLOYMENT_DIR/$instance"
        docker-compose down
    done

    echo -e "\n✅ All instances stopped successfully!"
}

function restart_all() {
    print_header "🔄 Restarting All OpenClaw Instances" 0
    stop_all
    sleep 2
    start_all
}

function status_all() {
    print_header "📊 Status of All OpenClaw Instances" 0

    echo -e "Container Status:"
    docker ps -a --filter "name=openclaw-instance" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo -e "\n\n🌐 Gateway URLs:"
    for i in "${!INSTANCES[@]}"; do
        local instance="${INSTANCES[$i]}"
        local port=$((18789 + i))
        echo -e "${COLORS[$i]}  $instance: http://localhost:$port${NC}"
    done
}

function logs_all() {
    print_header "📜 Viewing Logs for All Instances" 0

    echo "Press Ctrl+C to stop viewing logs"
    sleep 2

    # Follow logs from all containers
    docker-compose -f "$DEPLOYMENT_DIR/instance1/docker-compose.yml" \
                   -f "$DEPLOYMENT_DIR/instance2/docker-compose.yml" \
                   -f "$DEPLOYMENT_DIR/instance3/docker-compose.yml" \
                   logs -f --tail=50
}

function logs_instance() {
    local instance=$1
    if [ -z "$instance" ]; then
        echo "Usage: $0 logs <instance1|instance2|instance3>"
        return 1
    fi

    print_header "📜 Viewing Logs for $instance" 0
    cd "$DEPLOYMENT_DIR/$instance"
    docker-compose logs -f --tail=100
}

function shell_instance() {
    local instance=$1
    if [ -z "$instance" ]; then
        echo "Usage: $0 shell <instance1|instance2|instance3>"
        return 1
    fi

    print_header "🖥️  Opening Shell in $instance" 0
    docker exec -it "openclaw-$instance" bash
}

function setup_env_files() {
    print_header "⚙️  Setting Up Environment Files" 0

    for i in "${!INSTANCES[@]}"; do
        local instance="${INSTANCES[$i]}"
        if [ ! -f "$DEPLOYMENT_DIR/$instance/.env" ]; then
            echo -e "${COLORS[$i]}Creating .env for $instance${NC}"
            cp "$DEPLOYMENT_DIR/$instance/.env.example" "$DEPLOYMENT_DIR/$instance/.env"
            echo "   ✓ Created - Please edit and add your API keys"
        else
            echo -e "${COLORS[$i]}✓ .env already exists for $instance${NC}"
        fi
    done

    echo -e "\n📝 Next steps:"
    echo "1. Edit each instance's .env file and add your OpenRouter API keys"
    echo "2. Run: ./manage-all.sh start"
}

function update_all() {
    print_header "🔄 Updating All Instances" 0

    for i in "${!INSTANCES[@]}"; do
        local instance="${INSTANCES[$i]}"
        print_header "Updating $instance" $i
        cd "$DEPLOYMENT_DIR/$instance"
        docker-compose pull
        docker-compose down
        docker-compose up -d
    done

    echo -e "\n✅ All instances updated successfully!"
}

function health_check() {
    print_header "🏥 Health Check for All Instances" 0

    for i in "${!INSTANCES[@]}"; do
        local instance="${INSTANCES[$i]}"
        local port=$((18789 + i))
        echo -e "\n${COLORS[$i]}Checking $instance (port $port)...${NC}"

        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "  ✅ Healthy"
        else
            echo -e "  ❌ Unhealthy or not responding"
        fi
    done
}

function show_help() {
    cat << EOF
OpenClaw Multi-Instance Management Script

Usage: $0 <command> [options]

Commands:
    setup       - Create .env files from templates
    start       - Start all instances
    stop        - Stop all instances
    restart     - Restart all instances
    status      - Show status of all instances
    logs        - View logs from all instances
    logs <name> - View logs from specific instance (instance1, instance2, instance3)
    shell <name>- Open shell in specific instance
    update      - Pull latest images and restart all instances
    health      - Check health of all instances
    help        - Show this help message

Examples:
    $0 setup               # First time setup
    $0 start               # Start all instances
    $0 logs instance1      # View logs for instance1
    $0 shell instance2     # Open shell in instance2
    $0 health              # Check health of all instances

EOF
}

# Main script logic
case "${1:-}" in
    setup)
        setup_env_files
        ;;
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        status_all
        ;;
    logs)
        if [ -n "${2:-}" ]; then
            logs_instance "$2"
        else
            logs_all
        fi
        ;;
    shell)
        shell_instance "$2"
        ;;
    update)
        update_all
        ;;
    health)
        health_check
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: ${1:-}"
        echo ""
        show_help
        exit 1
        ;;
esac
