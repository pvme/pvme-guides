#!/bin/sh

time=$(date +%s)
week=$(( ($time / 86400 + 1) / 7 % 6))

cd "${0%/*}"

case $week in
  1)
      cp Duo_Ceilings_combined.txt vorago-basic.txt
    ;;
  2)
      cp Duo_Scop_combined.txt vorago-basic.txt
    ;;
  3)
      cp Duo_Vit_combined.txt vorago-basic.txt
    ;;
  4)
      cp Duo_GB_combined.txt vorago-basic.txt
    ;;
  5)
      cp Duo_TS_combined.txt vorago-basic.txt
    ;;
  0)
      cp Duo_PB_combined.txt vorago-basic.txt
    ;;
esac

git config user.name "PvM Encyclopedia"
git config user.email "a"
git add .
git commit -m 'Update vorago-basic.txt'
git push origin master:update-vorago-basic --force

echo https://api.github.com/repos/$GITHUB_REPOSITORY/pulls

pr=$(curl \
  -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/pulls" \
  -d '{"title":"Update vorago-basic.txt","body":"","head":"update-vorago-basic","base":"master"}' \
  )

if echo $pr | grep "A pull request already exists"
then
    echo "PR already exists"
    exit
fi

pr_url=$(echo $pr | grep -Po "https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/\d+" | head -n1 | cut -d " " -f1)

sleep 30

curl \
  -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -d '{"merge_method":"squash"}' \
  $pr_url/merge
