以下をUbuntuのターミナルで順番に実行してください。
Docker公式のUbuntu向け手順に沿った入れ方です。([Docker Documentation][1])

## 1. 既存パッケージを更新

```bash
sudo apt update
sudo apt install -y ca-certificates curl
```

## 2. Docker公式GPGキーを追加

```bash
sudo install -m 0755 -d /etc/apt/keyrings

sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

sudo chmod a+r /etc/apt/keyrings/docker.asc
```

## 3. Docker公式リポジトリを追加

```bash
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```

## 4. Dockerをインストール

```bash
sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 5. Dockerの起動確認

```bash
sudo systemctl status docker
```

`active (running)` と出ていればOKです。

## 6. テスト実行

```bash
sudo docker run hello-world
```

`Hello from Docker!` と表示されればインストール成功です。([Docker Documentation][1])

---

## 7. sudoなしでdockerを使えるようにする

毎回 `sudo docker ...` と打つのが面倒な場合は、ユーザーを `docker` グループに追加します。

```bash
sudo usermod -aG docker $USER
```

その後、いったんログアウトして再ログインしてください。
SSH接続なら、いったん切断して入り直します。

入り直したら確認します。

```bash
docker run hello-world
```

これで `sudo` なしで動けば完了です。

---

## Docker Composeの確認

最近のDockerでは `docker-compose` ではなく、基本は以下です。

```bash
docker compose version
```

このようにスペースありです。

```bash
docker compose up -d
```

まずはここまで入れれば、Ubuntu上でDocker環境は使える状態になります。

[1]: https://docs.docker.com/engine/install/ubuntu/?utm_source=chatgpt.com "Install Docker Engine on Ubuntu"
