# SALT IMPORT TERMINAL · DAEYANG

(주)대양 소금 수입동향 대시보드입니다. 관세청 「품목별 국가별 수출입실적(GW)」 API에서 파키스탄·중국·호주산 소금(HSK 2501, 10단위 5개 세번)의 월별 수입 중량과 금액(CIF)을 받아 보여줍니다.

- `site/` — 대시보드 웹페이지 (GitHub Pages로 공개)
- `site/data/salt_import_data.csv` — 대시보드가 읽는 자료
- `scripts/fetch_kcs.py` — 관세청 API 수집 스크립트
- `.github/workflows/update-data.yml` — 매일 08:07(KST) 자동 수집 → 사이트 갱신
- `.github/workflows/deploy-on-push.yml` — `site/` 파일을 고치면 사이트 다시 올리기

## 처음 설정 (한 번만)

1. **저장소 만들기**: GitHub 오른쪽 위 `+` → **New repository** → 이름 `salt-import-terminal`, **Public** 선택 → **Create repository**.
2. **파일 올리기**: 저장소 화면의 **uploading an existing file** 링크(또는 **Add file → Upload files**)를 누르고, 압축을 푼 폴더 안의 내용물(`site`, `scripts`, `.github`, `README.md`)을 모두 끌어다 놓은 뒤 **Commit changes**.
   - `.github` 폴더는 숨김 폴더라 안 보일 수 있습니다. Mac은 Finder에서 `Cmd + Shift + .`, Windows는 탐색기 **보기 → 숨긴 항목** 체크.
3. **인증키 넣기**: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `KCS_SERVICE_KEY`
   - Secret: 공공데이터포털 인증키(Decoding 형태)
4. **사이트 켜기**: **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택.
5. **첫 실행**: **Actions** 탭 → (처음이면 활성화 버튼 누르기) → 왼쪽 **관세청 소금 수입자료 매일 갱신** → **Run workflow**.
6. 초록색 체크가 뜨면 사이트 주소에서 확인합니다:
   `https://<GitHub아이디>.github.io/salt-import-terminal/`

이후에는 매일 오전 8시경 자동으로 수집·갱신됩니다. 실패하면 GitHub이 가입 이메일로 알려줍니다.

## 알아둘 점

- 무료 GitHub Pages는 **공개 사이트**입니다. 주소를 아는 사람은 누구나 볼 수 있습니다(인증키는 Secrets에 있어 노출되지 않음).
- 금액은 관세청 수입통계 기준 **CIF**(운임·보험료 포함)입니다.
- 공공데이터포털 개발계정 인증키는 활용기간이 있으니 만료 전에 연장하세요. 연장 후 키가 바뀌면 3번만 다시 하면 됩니다.
- 국가·세번을 바꾸려면 `scripts/fetch_kcs.py` 위쪽의 `COUNTRIES`, `ITEMS`를 수정합니다.
