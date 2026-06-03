"""Đăng ký / gỡ tác vụ Windows Task Scheduler chạy sync_obsidian.bat định kỳ.

Đăng ký qua file XML (UTF-16) thay vì schtasks /TR, để path có khoảng trắng +
tiếng Việt được lưu chính xác (tránh lỗi 0x80070002 do path bị cắt ở dấu cách,
và lỗi code page khi gõ schtasks tay).

Dùng:
  python scripts/install_task.py            # tạo task chạy mỗi 6 giờ
  python scripts/install_task.py --remove   # gỡ task
"""
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TASK_NAME = "HermesObsidianSync"
REPO = Path(__file__).resolve().parent.parent
BAT = REPO / "scripts" / "sync_obsidian.bat"

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Sync Obsidian vault -> Supabase obsidian_vault (Hermes OS)</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{start}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
      <Repetition>
        <Interval>PT6H</Interval>
        <Duration>P1D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Enabled>true</Enabled>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{bat}</Command>
      <WorkingDirectory>{repo}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def main() -> None:
    if "--remove" in sys.argv:
        sys.exit(subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]).returncode)

    if not BAT.is_file():
        raise SystemExit(f"Không thấy {BAT}")

    start = datetime.now().replace(microsecond=0).isoformat()
    xml = XML_TEMPLATE.format(start=start, bat=str(BAT), repo=str(REPO))

    # schtasks /XML đọc file UTF-16.
    with tempfile.NamedTemporaryFile("w", suffix=".xml", encoding="utf-16",
                                     delete=False) as fh:
        fh.write(xml)
        xml_path = fh.name

    rc = subprocess.run(
        ["schtasks", "/Create", "/TN", TASK_NAME, "/XML", xml_path, "/F"]
    ).returncode
    Path(xml_path).unlink(missing_ok=True)

    if rc == 0:
        print(f"\nĐã đăng ký task '{TASK_NAME}' (mỗi 6 giờ, chạy khi máy bật).")
        print(f"  Chạy thử: schtasks /Run   /TN {TASK_NAME}")
        print(f"  Gỡ:       python scripts/install_task.py --remove")
    sys.exit(rc)


if __name__ == "__main__":
    main()
