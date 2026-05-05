# MaskSource GitHub 推送脚本
# 使用方式：在 MaskSource 目录下右键 → 使用 PowerShell 运行

param(
    [Parameter(Mandatory=$true)]
    [string]$GithubUsername,

    [Parameter(Mandatory=$false)]
    [string]$RepoName = "MaskSource"
)

$remoteUrl = "https://github.com/$GithubUsername/$RepoName.git"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "MaskSource GitHub 推送脚本" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "GitHub 用户名: $GithubUsername"
Write-Host "仓库名称: $RepoName"
Write-Host "远程地址: $remoteUrl"
Write-Host ""

# 检查是否在 git 仓库内
if (-not (Test-Path ".git")) {
    Write-Error "当前目录不是 git 仓库，请先运行 git init"
    exit 1
}

# 检查远程是否已绑定
$remotes = git remote -v 2>$null
if ($remotes -match "origin") {
    Write-Host "检测到已有 remote origin，正在更新..." -ForegroundColor Yellow
    git remote set-url origin $remoteUrl
} else {
    Write-Host "绑定远程仓库..." -ForegroundColor Green
    git remote add origin $remoteUrl
}

# 确保分支名为 main
git branch -M main

Write-Host ""
Write-Host "正在推送到 GitHub..." -ForegroundColor Green
Write-Host "（首次推送会提示输入 GitHub 用户名和密码/Token）" -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "推送成功！" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "仓库地址: $remoteUrl"
    Write-Host "Pages 地址: https://$GithubUsername.github.io/$RepoName/"
    Write-Host ""
    Write-Host "下一步：开启 GitHub Pages" -ForegroundColor Cyan
    Write-Host "1. 打开 $remoteUrl/settings/pages"
    Write-Host "2. Source → Deploy from a branch"
    Write-Host "3. Branch: main / folder: /docs"
    Write-Host "4. 点击 Save，等待 1~3 分钟"
} else {
    Write-Host ""
    Write-Host "推送失败。可能的原因：" -ForegroundColor Red
    Write-Host "- GitHub 仓库尚未创建，请先去 https://github.com/new 创建空仓库" -ForegroundColor Yellow
    Write-Host "- 认证失败，请检查用户名和密码/Personal Access Token" -ForegroundColor Yellow
    Write-Host "- 网络问题" -ForegroundColor Yellow
}

Write-Host ""
Pause
