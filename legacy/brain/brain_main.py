from action_router import ActionRouter
from cli_input import read_user_text
from llm_pipeline import build_action_json
from llm_runtime import LLMRuntime
from network_probe import is_online


def main() -> None:
    runtime = LLMRuntime()
    handles = runtime.initialize()
    router = ActionRouter(topic="/hylion/action_json")
    try:
        router.start()
    except RuntimeError as exc:
        print(f"[System]: {exc}")
        return

    print("HYlion Brain minimal loop started. Type 'exit' to stop.")

    try:
        while True:
            user_text = read_user_text()
            if not user_text:
                continue
            if user_text.lower() in {"exit", "quit"}:
                print("Shutting down.")
                break

            online = is_online()
            action_json = build_action_json(user_text, online=online, handles=handles)

            if not online:
                print("[System]: 인터넷 연결 안됨")
            else:
                router.publish_action(action_json)
                print("[System]: /hylion/action_json 토픽으로 발행 완료")

            print(f"[HYlion]: {action_json.get('reply_text', '')}")
    finally:
        router.close()


if __name__ == "__main__":
    main()
