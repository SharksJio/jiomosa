#!/bin/bash
# Docker Helper Script for Codespaces
# Automatically adds sudo when needed

COMPOSE_CMD="sudo docker compose"

case "$1" in
  up)
    $COMPOSE_CMD up -d
    ;;
  down)
    $COMPOSE_CMD down
    ;;
  restart)
    $COMPOSE_CMD restart "${@:2}"
    ;;
  ps|status)
    $COMPOSE_CMD ps
    ;;
  logs)
    $COMPOSE_CMD logs "${@:2}"
    ;;
  build)
    $COMPOSE_CMD build "${@:2}"
    ;;
  exec)
    $COMPOSE_CMD exec "${@:2}"
    ;;
  *)
    echo "Usage: $0 {up|down|restart|ps|logs|build|exec} [options]"
    echo ""
    echo "Examples:"
    echo "  $0 up              # Start all services"
    echo "  $0 down            # Stop all services"
    echo "  $0 ps              # Show service status"
    echo "  $0 logs renderer   # View renderer logs"
    echo "  $0 restart chrome  # Restart chrome service"
    exit 1
    ;;
esac
