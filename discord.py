import discord
import serial
import asyncio

# 디스코드 봇과 시리얼 통신 설정
TOKEN = "TOKEN"  # 디스코드 봇 토큰
SERIAL_PORT = "COM4"              # 아두이노가 연결된 포트 (알맞게 변경하기)
BAUD_RATE = 9600                  # 아두이노 시리얼 통신 속도

# Intents 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

# 전역 변수
alert_temp = None  # 기준 온도
alert_humi = None  # 기준 습도
alert_user = None  # 경고를 받을 사용자
latest_temp = None  # 최신 온도
latest_humi = None  # 최신 습도
alert_channel = None  # 경고 메시지를 보낼 채널


# 시리얼 통신 초기화
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    print(f"아두이노와 연결 성공: {SERIAL_PORT} @ {BAUD_RATE}")
except Exception as e:
    print(f"아두이노와 연결 실패: {e}")
    ser = None


@client.event
async def on_ready():
    print(f"디스코드 봇 로그인 완료: {client.user}")


@client.event
async def on_message(message):
    global alert_temp, alert_humi, alert_user, latest_temp, latest_humi, alert_channel

    if message.author == client.user:
        return

    # 디버깅: 받은 메시지 출력
    print(f"받은 메시지: {message.content}")

    # !temp 명령어: 온습도 확인 및 데이터 저장
    if message.content.startswith("!temp"):
        print("!temp 명령 감지됨")
        if ser is None:
            await message.channel.send("⚠️ 아두이노와 연결되지 않았습니다!")
            return

        try:
            ser.write(b'1')  # 아두이노로 온습도 요청
            await asyncio.sleep(1)

            if ser.in_waiting > 0:
                data = ser.readline().decode().strip()
                print(f"아두이노 데이터: {data}")  # 디버깅 메시지

                # 데이터 파싱 및 저장
                try:
                    latest_temp, latest_humi = map(float, data.split(","))
                    formatted_message = (
                        f"🌡️ 현재 온도: **{latest_temp:.1f}°C**\n"
                        f"💧 현재 습도: **{latest_humi:.1f}%**"
                    )
                    await message.channel.send(formatted_message)
                except ValueError:
                    await message.channel.send(f"⚠️ 데이터를 처리할 수 없습니다: {data}")
            else:
                await message.channel.send("⚠️ 아두이노에서 응답이 없습니다!")
        except Exception as e:
            await message.channel.send(f"⚠️ 아두이노와 통신 중 오류 발생: {e}")

    # !alert 명령어: 경고 기준 및 채널 설정
    elif message.content.startswith("!alert"):
        print("!alert 명령 감지됨")
        try:
            parts = message.content.split()
            if len(parts) != 3:
                await message.channel.send("⚠️ 사용법: !alert <온도 기준> <습도 기준>")
                return

            alert_temp = float(parts[1])
            alert_humi = float(parts[2])
            alert_user = message.author  # 기준치를 설정한 사용자 저장
            alert_channel = message.channel  # 메시지를 보낼 채널 저장
            print(f"설정된 경고 기준: 온도={alert_temp}, 습도={alert_humi}, 채널={alert_channel.name}")
            await message.channel.send(
                f"✅ {alert_user.mention}, 경고 기준 설정 완료:\n"
                f"온도 > {alert_temp}°C, 습도 > {alert_humi}%"
            )
        except ValueError:
            await message.channel.send("⚠️ 잘못된 입력입니다. 숫자로 기준치를 설정해주세요.")

    # !alert off 명령어: 경고 기준 해제
    elif message.content.startswith("!alert off"):
        alert_temp = None
        alert_humi = None
        alert_user = None
        alert_channel = None
        print("경고 기준 해제됨")
        await message.channel.send("✅ 경고 기준이 해제되었습니다.")


async def monitor_temperature():
    global alert_temp, alert_humi, alert_user, latest_temp, latest_humi, alert_channel

    while True:
        if ser is not None and alert_temp is not None and alert_humi is not None:
            try:
                # 아두이노로 데이터 요청
                ser.write(b'1')
                await asyncio.sleep(1)

                if ser.in_waiting > 0:
                    data = ser.readline().decode().strip()
                    print(f"아두이노 데이터: {data}")  # 디버깅 메시지
                    try:
                        latest_temp, latest_humi = map(float, data.split(","))
                        print(f"최신 데이터 업데이트: 온도={latest_temp}, 습도={latest_humi}")
                    except ValueError:
                        print(f"데이터 파싱 오류: {data}")
                        continue

                # 기준치 초과 확인
                if latest_temp is not None and latest_humi is not None:
                    print(f"디버깅: 최신 온도 = {latest_temp}, 최신 습도 = {latest_humi}")
                    print(f"디버깅: 기준 온도 = {alert_temp}, 기준 습도 = {alert_humi}")

                    if latest_temp > alert_temp or latest_humi > alert_humi:
                        print("경고 조건 충족!")  # 조건 충족 디버깅
                        if alert_user and alert_channel:
                            print(f"경고 메시지를 보낼 사용자: {alert_user}")  # 사용자 정보 확인
                            await alert_channel.send(
                                f"🚨 {alert_user.mention} 경고! 현재 온도: {latest_temp:.1f}°C, 습도: {latest_humi:.1f}%\n"
                                f"기준 초과: 온도 > {alert_temp}°C 또는 습도 > {alert_humi}%"
                            )
                    else:
                        print("경고 조건 미충족.")
            except Exception as e:
                print(f"⚠️ 오류 발생: {e}")

        await asyncio.sleep(10)  # 10초마다 데이터 확인


# 봇 실행 및 모니터링 작업 추가
async def main():
    task1 = asyncio.create_task(client.start(TOKEN))
    task2 = asyncio.create_task(monitor_temperature())
    await asyncio.gather(task1, task2)

asyncio.run(main())
