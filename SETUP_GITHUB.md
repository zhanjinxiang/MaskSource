# GitHub 仓库创建与推送指南

本地仓库已初始化并完成首次提交。下面是将代码推送到 GitHub 并开启 Pages 的完整步骤。

---

## 方式一：GitHub 网页创建（推荐，最快）

### Step 1：在 GitHub 创建空仓库

1. 打开 https://github.com/new
2. 填写信息：
   - **Repository name**: `MaskSource`
   - **Description**: 基于「双盾双溯源」的视觉语言模型全链路版权保护体系
   - **Visibility**: 建议选 `Public`（Pages 免费且方便展示）
3. **不要勾选** "Initialize this repository with a README"（本地已有）
4. 点击 **Create repository**

### Step 2：绑定远程并推送

在本地 `MaskSource/` 目录下打开 PowerShell / Git Bash，执行：

```bash
# 绑定远程仓库（把 your-team 换成你的 GitHub 用户名/组织名）
git remote add origin https://github.com/your-team/MaskSource.git

# 推送
git branch -M main
git push -u origin main
```

---

## 方式二：GitHub CLI 一键创建

如果已安装 [GitHub CLI](https://cli.github.com/) 并登录：

```bash
# 创建远程仓库并推送
gh repo create MaskSource --public --source=. --remote=origin --push
```

---

## 开启 GitHub Pages

推送完成后，在仓库页面操作：

1. 进入仓库 → **Settings** → **Pages**（左侧栏）
2. **Source** 选择 **Deploy from a branch**
3. **Branch** 选择 `main`，文件夹选择 `/docs`
4. 点击 **Save**
5. 等待 1~3 分钟，访问 `https://your-team.github.io/MaskSource/`

> 本仓库已配置 `docs/.nojekyll` 文件，确保 Pages 正确渲染。

---

## 后续更新推送

```bash
git add .
git commit -m "update: xxx"
git push origin main
```

---

## 检查清单

- [ ] GitHub 远程仓库已创建
- [ ] 代码已推送到 `main` 分支
- [ ] GitHub Pages 已开启，指向 `/docs`
- [ ] 主页 `https://your-team.github.io/MaskSource/` 可正常打开
- [ ] README 中的 GitHub 链接已替换为真实地址
- [ ] docs/index.html 中的 GitHub 链接已替换为真实地址
