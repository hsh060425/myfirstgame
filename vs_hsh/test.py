import sys, os
def resource_path(relative_path):
    """개발 중과 빌드 후 모두 동작하는 경로 반환"""
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, relative_path)

print(resource_path("assets/player.png"))
print(hasattr(sys, '_MEIPASS'))

print(hasattr(sys, '_MEIPASS'))
# True
