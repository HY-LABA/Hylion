# Orin IP 변경 방법

시연장에서 Orin IP가 바뀌면 `~/.ssh/config` 파일의 `orin` HostName을 수정한다.

## 수정할 줄

```
Host orin
    HostName 172.16.146.4  ← 이 IP를 새 IP로 변경
```

## 파일 여는 방법

**VSCode:**
`Ctrl + P` → `~/.ssh/config` 입력 → Enter

```

## Orin에서 IP 확인

Orin 터미널에서:
```bash
hostname -I(가장 처음에 뜨는거)
```