# B-G431B-ESC1 공장초기화 / Flash 전체 삭제 가이드

이 문서는 STMicroelectronics의 `B-G431B-ESC1` 보드에 들어 있는 STM32 Flash를 전체 삭제하는 방법을 설명합니다.

여기서 말하는 "공장초기화"는 정확히는 **MCU 내부 Flash 전체 삭제(Mass erase / Full chip erase)** 입니다. 삭제 후에는 기존 펌웨어가 사라지므로, 보드는 새 펌웨어를 다시 올리기 전까지 ESC나 모터 제어 동작을 하지 않습니다.

## 준비물

- B-G431B-ESC1 보드
- PC
- Micro USB 케이블
- STM32CubeProgrammer

## 시작 전 주의사항

Flash 삭제 자체는 모터를 직접 구동하는 작업이 아니지만, B-G431B-ESC1은 모터 제어용 ESC 보드이므로 안전하게 진행해야 합니다.

작업 전에 아래 상태인지 확인합니다.

- 배터리 또는 DC 전원이 연결되어 있지 않음
- USB만 연결할 예정임
- 모터에 프로펠러, 팬, 날개 같은 위험한 부하가 없음
- 모터가 외부 힘으로 회전하고 있지 않음
- 가능하면 전원 제거 후 잠시 기다려 커패시터가 방전된 상태임

모터 3상선은 가능하면 분리하는 것이 좋지만, **배터리/DC 전원이 연결되어 있지 않다면 모터가 연결된 상태에서도 Flash 삭제는 보통 문제 없습니다.**

가장 중요한 것은 **배터리 또는 DC 버스 전원을 연결하지 않는 것**입니다.

## 1. 보드 연결

1. B-G431B-ESC1 보드에 배터리/DC 전원이 연결되어 있지 않은지 확인합니다.
2. Micro USB 케이블로 보드와 PC를 연결합니다.
3. STM32CubeProgrammer를 실행합니다.

## 2. CubeProgrammer에서 Connect

1. 오른쪽 상단 연결 방식이 `ST-LINK`인지 확인합니다.
2. Port가 `SWD`인지 확인합니다.
3. `Connect` 버튼을 누릅니다.

정상 연결되면 화면 오른쪽에 다음과 비슷한 정보가 표시됩니다.

```text
Connected
Board: B-G431B-ESC1
Device: STM32G43x/G44x
NVM size: 128 KB
CPU: Cortex-M4
Target voltage: 약 3.2 V
```

이 정보가 보이면 보드와 MCU가 정상적으로 연결된 것입니다.

## 3. Erasing & Programming 화면으로 이동

1. 왼쪽 메뉴에서 `Erasing & Programming` 화면으로 이동합니다.
2. 화면 가운데/오른쪽에 `Erase flash memory` 탭이 보이는지 확인합니다.
3. `Erase external memory`가 아니라 **`Erase flash memory`** 탭을 사용해야 합니다.

## 4. Full chip erase 실행

`Start Programming` 버튼을 누르지 않습니다.

파일을 다운로드하는 것이 아니라 Flash를 지우는 작업이므로, 오른쪽의 `Erase flash memory` 영역에서 실행해야 합니다.

1. `Erase flash memory` 탭 안에 있는 **`Full chip era...`** 버튼을 누릅니다.
2. 확인 팝업이 뜨면 `Yes` 또는 `OK`를 누릅니다.
3. 아래 Log 창을 확인합니다.

성공하면 Log에 다음 메시지가 표시됩니다.

```text
Mass erase successfully achieved
```

이 메시지가 나오면 Flash 전체 삭제가 성공한 것입니다.

## 5. 자주 나오는 오류

### Empty file path 오류

만약 다음과 같은 오류가 뜨면:

```text
Empty file path, please select the file to be loaded
```

이것은 `Start Programming` 버튼을 눌렀기 때문입니다.

해결 방법:

1. 오류 창에서 `OK`를 누릅니다.
2. 왼쪽의 `Start Programming` 버튼을 누르지 않습니다.
3. 오른쪽 `Erase flash memory` 탭의 **`Full chip era...`** 버튼을 누릅니다.

## 6. 삭제 완료 후 연결 해제

삭제 성공 메시지를 확인한 뒤:

1. 오른쪽 상단의 `Disconnect` 버튼을 누릅니다.
2. USB 케이블을 분리합니다.

이제 보드는 Flash가 지워진 빈 상태입니다.

## 7. 정말 지워졌는지 확인하는 방법

성공 메시지만으로도 보통 충분하지만, 직접 확인하고 싶다면 Flash 메모리를 읽어보면 됩니다.

1. 다시 USB로 보드를 연결합니다.
2. STM32CubeProgrammer에서 `Connect`를 누릅니다.
3. 왼쪽 메뉴에서 메모리 보기 화면으로 이동합니다.
4. 주소를 다음처럼 설정합니다.

```text
Address: 0x08000000
Size: 0x100 또는 1024
```

5. `Read`를 누릅니다.

삭제된 Flash는 보통 값이 전부 `FF`로 보입니다.

```text
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
```

B-G431B-ESC1의 Flash는 128 KB이므로 대략 다음 범위가 내부 Flash 영역입니다.

```text
0x08000000 ~ 0x0801FFFF
```

다음 주소들을 몇 군데 읽어 봤을 때 모두 `FF`로 보이면 삭제가 잘 된 것입니다.

```text
0x08000000
0x08001000
0x08010000
0x0801F000
```

## 8. 삭제 후 상태

Flash 삭제 후 보드는 다음 상태가 됩니다.

- 기존 펌웨어 없음
- ESC/모터 제어 동작 없음
- 배터리를 연결해도 기존처럼 동작하지 않음
- 새 펌웨어를 올려야 다시 사용 가능

새 펌웨어를 올린 뒤 처음 배터리/DC 전원을 연결할 때는 특히 주의해야 합니다.

- PWM 설정
- 게이트 드라이버 enable 설정
- 전류 제한
- 모터 파라미터
- 회전 방향

위 설정이 잘못되어 있으면 모터가 갑자기 돌거나 보드에 과전류가 흐를 수 있습니다.

## 요약

가장 짧게 정리하면:

```text
배터리/DC 전원 제거
USB만 연결
STM32CubeProgrammer 실행
ST-LINK로 Connect
Erasing & Programming 이동
Erase flash memory 탭 선택
Full chip era... 클릭
Mass erase successfully achieved 확인
Disconnect
USB 분리
```

