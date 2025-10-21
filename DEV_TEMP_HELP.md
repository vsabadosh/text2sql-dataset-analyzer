## Clean command
find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
find . -name '__pycache__' -type d -prune -exec rm -rf {} +

##GIT (TODO:  will be removed. Security issue)
git push -u origin HEAD
access key: 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
