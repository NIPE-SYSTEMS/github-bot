#!/bin/sh

docker run --detach --restart=always --name github-bot \
    -v /root/github-bot/config.yml:/app/config.yml \
    -p 8080:8080 github-bot
