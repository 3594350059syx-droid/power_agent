<template>
  <div class="landing-page">
    <header class="landing-nav">
      <button class="brand-mark" type="button" aria-label="返回首页" @click="scrollToTop">
        <span class="brand-symbol" aria-hidden="true">
          <i></i><i></i><i></i>
        </span>
        <span class="brand-lockup">
          <strong>NEXUS</strong>
          <small>INDUSTRIAL INTELLIGENCE</small>
        </span>
      </button>

      <nav class="nav-links" aria-label="主导航">
        <a href="#capabilities">能力矩阵</a>
        <a href="#story">关于平台</a>
        <button class="nav-console" type="button" @click="goTo('/dashboard')">
          进入监控台
          <span aria-hidden="true">↗</span>
        </button>
      </nav>
    </header>

    <main class="hero-frame">
      <section class="hero-visual" aria-label="数字孪生工厂演示">
        <div class="visual-ruler ruler-top" aria-hidden="true">
          <span>FIELD / 03</span>
          <span>31° 14' 08'' N</span>
        </div>
        <div class="visual-ruler ruler-bottom" aria-hidden="true">
          <span>LIVE TWIN / 2026</span>
          <span class="ruler-line"></span>
          <span>07:42:16</span>
        </div>

        <div class="blue-orbit orbit-one" aria-hidden="true"></div>
        <div class="blue-orbit orbit-two" aria-hidden="true"></div>
        <div class="crosshair crosshair-a" aria-hidden="true"><span></span></div>
        <div class="crosshair crosshair-b" aria-hidden="true"><span></span></div>

        <svg class="factory-ghost" viewBox="0 0 760 600" fill="none" aria-hidden="true">
          <defs>
            <linearGradient id="ghostFill" x1="80" y1="60" x2="600" y2="520" gradientUnits="userSpaceOnUse">
              <stop stop-color="#d4e9f7" stop-opacity=".82" />
              <stop offset="1" stop-color="#edf6fb" stop-opacity=".18" />
            </linearGradient>
            <linearGradient id="ghostLine" x1="100" y1="100" x2="600" y2="450" gradientUnits="userSpaceOnUse">
              <stop stop-color="#7fc9f4" stop-opacity=".72" />
              <stop offset="1" stop-color="#2367c9" stop-opacity=".08" />
            </linearGradient>
          </defs>
          <path d="M83 454 291 293l196 92-207 164-197-95Z" fill="url(#ghostFill)" />
          <path d="m291 293 198-142 193 92-205 142-186-92Z" fill="#dceef8" fill-opacity=".64" />
          <path d="m487 385 205-142v104L487 500V385Z" fill="#c8e2f2" fill-opacity=".42" />
          <path d="m83 454 207 95V425l-207-92v121Z" fill="#e9f5fa" fill-opacity=".75" />
          <path d="m290 425 197 91V385l-197-92v132Z" fill="#c1dfef" fill-opacity=".49" />
          <path d="m289 293 199 92v131M487 385l205-142M83 454l207 95 205-142" stroke="url(#ghostLine)" stroke-width="2" />
          <path d="m152 362 138-105 127 59-138 106-127-60ZM386 251l110-77 122 57-112 79-120-59Z" stroke="#91cbe8" stroke-opacity=".7" stroke-width="2" />
          <path d="m180 350 82-63 84 39-84 65-82-41ZM414 244l75-52 77 36-75 54-77-38Z" fill="#fff" fill-opacity=".46" />
          <path d="M310 441v-89l35 17v89l-35-17ZM366 467v-89l35 17v89l-35-17ZM229 480v-63l27 13v63l-27-13ZM554 400v-60l27-19v61l-27 18Z" fill="#2367c9" fill-opacity=".17" />
          <path d="M326 264v-61M353 277v-70M377 288v-62M326 203l27 12 24-10" stroke="#70bce6" stroke-width="2" />
          <path d="M535 247v-99M558 258v-96M580 269v-89M524 148h76" stroke="#2367c9" stroke-opacity=".42" stroke-width="2" />
          <path d="m98 500 191 87 201-143M114 517l177 81 216-154" stroke="#92cce8" stroke-opacity=".42" />
          <circle cx="489" cy="385" r="6" fill="#38bdf2" />
          <circle cx="489" cy="385" r="14" stroke="#38bdf2" stroke-opacity=".35" />
        </svg>

        <div class="route-line route-line-one" aria-hidden="true"><span></span></div>
        <div class="route-line route-line-two" aria-hidden="true"><span></span></div>

        <div class="phone-stage">
          <div class="phone-shadow" aria-hidden="true"></div>
          <div class="phone-device">
            <div class="phone-button phone-button-top" aria-hidden="true"></div>
            <div class="phone-button phone-button-mid" aria-hidden="true"></div>
            <div class="phone-screen">
              <div class="screen-status">
                <span>09:41</span>
                <span class="status-icons"><i></i><i></i><b></b></span>
              </div>
              <div class="screen-nav">
                <span class="screen-logo"><i></i><i></i><i></i></span>
                <span>现场总览</span>
                <span class="screen-menu">•••</span>
              </div>
              <div class="screen-heading">
                <div>
                  <small>PLANT 04 / EAST WING</small>
                  <strong>生产态势</strong>
                </div>
                <span class="live-chip"><i></i> LIVE</span>
              </div>

              <div class="twin-map">
                <div class="map-grid" aria-hidden="true"></div>
                <div class="map-topbar" aria-hidden="true">
                  <span><i></i> LIVE FLOORPLAN</span>
                  <b>04 / EAST WING</b>
                </div>
                <svg viewBox="0 0 280 218" fill="none" aria-label="工厂数字孪生地图">
                  <path d="m32 159 74-54 53 23 78-54 38 19-72 60-47-22-73 51-51-23Z" fill="#17376c" stroke="#3982d6" stroke-opacity=".7" />
                  <path d="m76 128 36-26 27 12-36 27-27-13ZM155 132l45-32 23 12-45 34-23-14ZM111 171l35-26 25 9-37 29-23-12Z" fill="#27538e" stroke="#69c7f1" stroke-opacity=".64" />
                  <path d="M32 159V84h45l17-22h48v24h48l28-28h39v55" stroke="#75c9ed" stroke-opacity=".62" stroke-width="1.5" stroke-dasharray="3 4" />
                  <path d="M43 85h41M101 85h32M151 85h33M205 65h42M51 143v-18M72 129v-17M234 112V88" stroke="#9fe0f7" stroke-opacity=".52" />
                  <path d="m42 151 37-27 22 10M168 128l33-24 18 9M119 165l27-20 15 6" stroke="#b8edff" stroke-opacity=".76" stroke-width="1.5" />
                  <path d="m85 118 33-24 26 12M164 125l42-30M123 163l35-25" stroke="#9fe0f7" stroke-opacity=".72" stroke-width="2" />
                  <path d="M53 52h48l24 18h44l28-22h50" stroke="#38bdf2" stroke-width="2" stroke-dasharray="4 6" />
                  <path d="m97 52-10 10M173 70l10-10M225 48l10 9" stroke="#38bdf2" stroke-width="2" />
                  <g fill="#9fe0f7" font-family="monospace" font-size="7" letter-spacing=".4">
                    <text x="43" y="78">LINE A</text>
                    <text x="188" y="80">ZONE 04</text>
                    <text x="80" y="151">A-01</text>
                    <text x="178" y="123">A-02</text>
                  </g>
                  <circle cx="115" cy="104" r="5" fill="#61d5a4" /><circle cx="115" cy="104" r="11" stroke="#61d5a4" stroke-opacity=".3" />
                  <circle cx="201" cy="100" r="5" fill="#f4b860" /><circle cx="201" cy="100" r="11" stroke="#f4b860" stroke-opacity=".3" />
                  <circle cx="145" cy="157" r="5" fill="#38bdf2" /><circle cx="145" cy="157" r="11" stroke="#38bdf2" stroke-opacity=".3" />
                </svg>
                <div class="map-label label-green"><i></i> 12 在线</div>
                <div class="map-label label-amber"><i></i> 1 关注</div>
                <span class="map-tooltip">设备群组 A-02 <b>98.4%</b></span>
                <div class="map-footer" aria-hidden="true"><span><i></i> 12 NODES ONLINE</span><b>SYNC 07:42:16</b></div>
              </div>

              <div class="screen-metrics">
                <article>
                  <span>综合健康度</span>
                  <strong>98.4<em>%</em></strong>
                  <small><i></i> 较昨日 +1.8%</small>
                </article>
                <article>
                  <span>实时负荷</span>
                  <strong>76.2<em>MW</em></strong>
                  <div class="mini-bars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
                </article>
              </div>

              <div class="screen-bottom">
                <span>数据同步中</span>
                <div class="sync-progress"><i></i></div>
                <b>24 ms</b>
              </div>
            </div>
          </div>
        </div>

        <div class="floating-card card-health">
          <span class="card-kicker"><i></i> ASSET HEALTH</span>
          <strong>98.4<span>%</span></strong>
          <small>全厂设备健康度</small>
          <div class="sparkline"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
        </div>
        <div class="floating-card card-sync">
          <span class="sync-icon">⌁</span>
          <div><strong>24<span>ms</span></strong><small>数据延迟</small></div>
          <b>SYNCED</b>
        </div>
      </section>

      <section id="story" class="hero-copy">
        <div class="copy-index" aria-hidden="true">01<span>/03</span></div>
        <div class="copy-content">
          <p class="eyebrow"><span></span> DIGITAL TWIN PLATFORM</p>
          <h1>让工厂，<br /><em>实时可见</em></h1>
          <p class="hero-description">连接生产、设备与运营数据，构建统一的数字化现场，让每一次决策都有迹可循。</p>

          <div id="capabilities" class="capability-list">
            <article v-for="item in capabilities" :key="item.index" class="capability-item">
              <span class="capability-index">{{ item.index }}</span>
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
              </div>
              <span class="capability-arrow" aria-hidden="true">↗</span>
            </article>
          </div>

          <div class="copy-actions">
            <button class="primary-action" type="button" @click="goTo('/dashboard')">
              <span>进入监控台</span><b aria-hidden="true">↗</b>
            </button>
            <button class="text-action" type="button" @click="goTo('/chat')">和 AI 助手聊聊 <span>→</span></button>
          </div>
          <div class="copy-meta"><span>POWERED BY NEXUS CORE</span><span>杭州 · 中国</span></div>
        </div>
      </section>
    </main>

    <footer class="landing-footer">
      <span>© 2026 NEXUS INDUSTRIAL INTELLIGENCE</span>
      <span class="footer-status"><i></i> SYSTEMS OPERATIONAL</span>
      <span>SCROLL TO EXPLORE <b>↓</b></span>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const capabilities = [
  { index: '01', title: '全域态势感知', description: '从生产现场到经营指标，一屏掌握关键变化。' },
  { index: '02', title: '设备健康预测', description: '以实时数据捕捉风险，在故障发生前行动。' },
  { index: '03', title: '智能协同决策', description: '让数据、模型与团队在同一个现场对话。' }
]

const goTo = path => router.push(path)

const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  background: #f3f6fa;
  color: #142b59;
  font-family: Manrope, "PingFang SC", "Microsoft YaHei", sans-serif;
}

:global(button),
:global(a) {
  font: inherit;
}

.landing-page {
  min-height: 100vh;
  overflow: hidden;
  background: #f3f6fa;
}

.landing-nav {
  width: min(1380px, calc(100% - 88px));
  height: 92px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  border: 0;
  padding: 0;
  color: #142b59;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.brand-symbol {
  position: relative;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: flex-end;
  gap: 3px;
  padding: 5px;
  background: #142b59;
  clip-path: polygon(0 0, 100% 0, 100% 72%, 72% 100%, 0 100%);
}

.brand-symbol i { display: block; width: 4px; background: #38bdf2; }
.brand-symbol i:nth-child(1) { height: 9px; opacity: .7; }
.brand-symbol i:nth-child(2) { height: 15px; }
.brand-symbol i:nth-child(3) { height: 20px; background: #fff; }

.brand-lockup { display: flex; flex-direction: column; gap: 2px; }
.brand-lockup strong { font-size: 15px; letter-spacing: .16em; line-height: 1; }
.brand-lockup small, .eyebrow, .visual-ruler, .landing-footer, .copy-meta, .screen-status, .screen-heading small, .card-kicker {
  font-family: "DM Mono", monospace;
  letter-spacing: .08em;
}
.brand-lockup small { font-size: 7px; color: #7090b0; letter-spacing: .14em; }

.nav-links { display: flex; align-items: center; gap: 35px; }
.nav-links a { color: #7186a2; font-size: 12px; text-decoration: none; transition: color .2s ease; }
.nav-links a:hover { color: #2367c9; }
.nav-console {
  border: 1px solid #bed1e3;
  border-radius: 2px;
  padding: 12px 16px;
  color: #142b59;
  background: transparent;
  font-size: 12px;
  cursor: pointer;
  transition: all .25s ease;
}
.nav-console span { margin-left: 14px; color: #2367c9; }
.nav-console:hover { color: #fff; background: #2367c9; border-color: #2367c9; transform: translateY(-2px); }
.nav-console:hover span { color: #fff; }

.hero-frame {
  width: min(1380px, calc(100% - 88px));
  min-height: min(730px, calc(100vh - 145px));
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(420px, .92fr);
  box-shadow: 0 28px 70px rgba(20, 43, 89, .12);
}

.hero-visual {
  position: relative;
  min-height: 730px;
  overflow: hidden;
  background-color: #eaf4fa;
  background-image: linear-gradient(rgba(35, 103, 201, .055) 1px, transparent 1px), linear-gradient(90deg, rgba(35, 103, 201, .055) 1px, transparent 1px);
  background-size: 36px 36px;
}
.hero-visual::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 44% 42%, rgba(255,255,255,.95), transparent 38%), linear-gradient(120deg, transparent 0 60%, rgba(119, 198, 233, .15) 60.1%, transparent 60.4%);
}
.visual-ruler { position: absolute; left: 34px; right: 34px; z-index: 3; display: flex; justify-content: space-between; color: #7e9bb7; font-size: 8px; }
.ruler-top { top: 28px; }
.ruler-bottom { bottom: 26px; align-items: center; }
.ruler-line { width: 44%; height: 1px; background: #a8c7dc; position: relative; }
.ruler-line::before, .ruler-line::after { content: ''; position: absolute; width: 4px; height: 4px; top: -2px; border: 1px solid #2367c9; background: #eaf4fa; }
.ruler-line::before { left: 0; }.ruler-line::after { right: 0; }

.factory-ghost { position: absolute; width: 76%; left: 21%; top: 18%; opacity: .82; z-index: 1; transform: rotate(-3deg); }
.blue-orbit { position: absolute; border: 1px solid rgba(56, 189, 242, .35); border-radius: 50%; z-index: 1; transform: rotate(-28deg); }
.orbit-one { width: 550px; height: 175px; left: 16%; top: 34%; }
.orbit-two { width: 350px; height: 112px; left: 31%; top: 42%; border-color: rgba(35, 103, 201, .2); }
.crosshair { position: absolute; width: 17px; height: 17px; z-index: 2; border: 1px solid #2367c9; opacity: .65; }
.crosshair::before, .crosshair::after, .crosshair span::before, .crosshair span::after { content: ''; position: absolute; background: #2367c9; }
.crosshair::before, .crosshair::after { top: 7px; width: 5px; height: 1px; }.crosshair::before { left: -5px; }.crosshair::after { right: -5px; }
.crosshair span::before, .crosshair span::after { left: 7px; width: 1px; height: 5px; }.crosshair span::before { top: -5px; }.crosshair span::after { bottom: -5px; }
.crosshair-a { left: 10%; top: 25%; }.crosshair-b { right: 10%; bottom: 21%; transform: rotate(45deg); }

.route-line { position: absolute; z-index: 2; height: 1px; transform-origin: left center; background: linear-gradient(90deg, #38bdf2, rgba(56,189,242,.05)); }
.route-line span { position: absolute; right: -3px; top: -3px; width: 7px; height: 7px; border-radius: 50%; background: #38bdf2; box-shadow: 0 0 0 5px rgba(56,189,242,.14); }
.route-line-one { width: 180px; left: 27%; top: 31%; transform: rotate(18deg); }
.route-line-two { width: 210px; left: 61%; top: 66%; transform: rotate(-32deg); background: linear-gradient(90deg, rgba(35,103,201,.08), #2367c9); }

.phone-stage { position: absolute; z-index: 4; left: 17%; top: 11%; width: min(375px, 45%); transform: rotate(-7deg); animation: phone-enter .9s cubic-bezier(.16, 1, .3, 1) both; }
.phone-shadow { position: absolute; width: 91%; height: 43px; bottom: -18px; left: 10%; border-radius: 50%; background: rgba(29, 65, 104, .22); filter: blur(16px); transform: rotate(7deg); }
.phone-device { position: relative; padding: 9px; border-radius: 42px; background: #102b57; box-shadow: 16px 24px 42px rgba(24, 61, 104, .27), inset 1px 1px 0 rgba(255,255,255,.4); }
.phone-device::before { content: ''; position: absolute; inset: 4px; border: 1px solid rgba(148, 206, 240, .32); border-radius: 39px; pointer-events: none; }
.phone-button { position: absolute; right: -3px; width: 4px; border-radius: 0 3px 3px 0; background: #2c5584; }
.phone-button-top { top: 117px; height: 44px; }.phone-button-mid { top: 177px; height: 70px; }
.phone-screen { position: relative; min-height: 648px; overflow: hidden; border-radius: 34px; padding: 22px 18px 17px; color: #d9f2ff; background: linear-gradient(160deg, #0c2450 0%, #102d5c 52%, #0b2049 100%); }
.phone-screen::after { content: ''; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(120deg, rgba(255,255,255,.11), transparent 20% 78%, rgba(56,189,242,.08)); }
.screen-status, .screen-nav, .screen-heading, .screen-metrics, .screen-bottom { position: relative; z-index: 1; }
.screen-status { display: flex; justify-content: space-between; color: #9bc5df; font-size: 8px; }
.status-icons { display: flex; align-items: center; gap: 5px; }.status-icons i { display: block; width: 8px; height: 5px; border: 1px solid #9bc5df; border-radius: 1px; }.status-icons i:nth-child(2) { width: 10px; }.status-icons b { width: 12px; height: 6px; border: 1px solid #9bc5df; border-radius: 2px; position: relative; }.status-icons b::after { content: ''; position: absolute; right: -3px; top: 1px; width: 2px; height: 2px; background: #9bc5df; }
.screen-nav { display: flex; align-items: center; gap: 8px; margin-top: 25px; color: #fff; font-size: 11px; font-weight: 600; }.screen-logo { display: flex; align-items: flex-end; gap: 2px; width: 17px; height: 17px; padding: 3px 2px; background: #2d76ca; }.screen-logo i { width: 2px; background: #b8ebff; }.screen-logo i:nth-child(1) { height: 5px; }.screen-logo i:nth-child(2) { height: 8px; }.screen-logo i:nth-child(3) { height: 11px; }.screen-menu { margin-left: auto; color: #7aa5ca; letter-spacing: 2px; }
.screen-heading { display: flex; justify-content: space-between; align-items: end; margin-top: 29px; }.screen-heading small { display: block; color: #6f9bbd; font-size: 6px; }.screen-heading strong { display: block; margin-top: 6px; color: #fff; font-size: 22px; letter-spacing: .02em; }.live-chip { padding: 5px 7px; color: #75dfb0; background: rgba(66, 197, 145, .12); font: 7px "DM Mono", monospace; letter-spacing: .08em; border: 1px solid rgba(117,223,176,.32); }.live-chip i, .footer-status i, .map-label i { display: inline-block; width: 5px; height: 5px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 3px rgba(117,223,176,.12); }
.twin-map { position: relative; height: 218px; margin-top: 21px; overflow: hidden; border: 1px solid rgba(114, 182, 224, .28); background: linear-gradient(145deg, rgba(21,63,114,.86), rgba(9,30,70,.42)); }.twin-map svg { position: relative; z-index: 1; width: 100%; height: 100%; }.map-grid { position: absolute; inset: 0; opacity: .34; background-image: linear-gradient(rgba(109,190,229,.15) 1px, transparent 1px), linear-gradient(90deg, rgba(109,190,229,.15) 1px, transparent 1px); background-size: 23px 23px; transform: perspective(160px) rotateX(42deg) scale(1.42); transform-origin: bottom; }.map-label { position: absolute; z-index: 2; padding: 4px 6px; font: 6px "DM Mono", monospace; color: #b7d9ec; background: rgba(10,31,71,.78); }.map-label i { margin-right: 4px; box-shadow: none; }.label-green { left: 12px; top: 13px; color: #75dfb0; }.label-amber { right: 12px; top: 48px; color: #f4b860; }.map-tooltip { position: absolute; z-index: 2; left: 54%; bottom: 23px; padding: 7px 9px; color: #9abbd3; background: #0b234d; font: 6px "DM Mono", monospace; box-shadow: 0 6px 15px rgba(0,0,0,.18); }.map-tooltip b { display: block; margin-top: 3px; color: #fff; font-size: 10px; }
.screen-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 11px; }.screen-metrics article { min-height: 96px; padding: 11px 10px; background: rgba(255,255,255,.065); border: 1px solid rgba(129,194,228,.15); }.screen-metrics span { display: block; color: #78a7c5; font: 7px "DM Mono", monospace; }.screen-metrics strong { display: block; margin-top: 7px; color: #fff; font: 500 22px "DM Mono", monospace; letter-spacing: -.06em; }.screen-metrics em { margin-left: 2px; color: #71c9ed; font-size: 9px; font-style: normal; letter-spacing: 0; }.screen-metrics small { display: block; margin-top: 7px; color: #74d7aa; font: 6px "DM Mono", monospace; }.screen-metrics small i { display: inline-block; width: 0; height: 0; margin-right: 3px; border-left: 3px solid transparent; border-right: 3px solid transparent; border-bottom: 4px solid currentColor; }.mini-bars { display: flex !important; align-items: end; gap: 2px; height: 16px; margin-top: 8px; }.mini-bars i { display: block; width: 7px; height: 7px; background: #2774bf; }.mini-bars i:nth-child(2) { height: 11px; }.mini-bars i:nth-child(3) { height: 8px; }.mini-bars i:nth-child(4) { height: 14px; background: #43b3dc; }.mini-bars i:nth-child(5) { height: 10px; }.mini-bars i:nth-child(6) { height: 16px; background: #43b3dc; }.mini-bars i:nth-child(7) { height: 13px; }
.screen-bottom { display: flex; align-items: center; gap: 7px; margin-top: 17px; color: #6d99b9; font: 6px "DM Mono", monospace; }.sync-progress { flex: 1; height: 2px; background: rgba(120,176,211,.2); }.sync-progress i { display: block; width: 82%; height: 100%; background: #38bdf2; }.screen-bottom b { color: #9cc5db; font-weight: 400; }

.floating-card { position: absolute; z-index: 5; color: #142b59; background: rgba(255,255,255,.92); border: 1px solid rgba(121,176,210,.36); box-shadow: 0 16px 32px rgba(48, 97, 139, .16); backdrop-filter: blur(10px); animation: card-enter 1s .24s cubic-bezier(.16,1,.3,1) both; }.card-health { top: 22%; right: 10%; width: 158px; padding: 15px 16px 13px; }.card-kicker { display: block; color: #7896af; font-size: 7px; }.card-kicker i { display: inline-block; width: 5px; height: 5px; margin-right: 5px; border-radius: 50%; background: #43c493; box-shadow: 0 0 0 3px rgba(67,196,147,.13); }.card-health strong { display: block; margin-top: 12px; font: 500 28px "DM Mono", monospace; letter-spacing: -.08em; }.card-health strong span { margin-left: 2px; color: #2367c9; font-size: 12px; }.card-health small { display: block; margin-top: 2px; color: #8aa0b6; font-size: 8px; }.sparkline { display: flex; align-items: end; gap: 3px; height: 20px; margin-top: 12px; }.sparkline i { width: 10px; height: 5px; background: #b8d9ea; transform: skew(-30deg); }.sparkline i:nth-child(2) { height: 9px; }.sparkline i:nth-child(3) { height: 7px; }.sparkline i:nth-child(4) { height: 13px; background: #63b9dd; }.sparkline i:nth-child(5) { height: 10px; }.sparkline i:nth-child(6) { height: 16px; background: #2367c9; }.sparkline i:nth-child(7) { height: 13px; }.sparkline i:nth-child(8) { height: 19px; background: #38bdf2; }
.card-sync { right: 8%; bottom: 20%; display: flex; align-items: center; gap: 9px; min-width: 140px; padding: 11px 13px; animation-delay: .38s; }.sync-icon { display: grid; place-items: center; width: 27px; height: 27px; color: #2367c9; background: #e6f3fa; border-radius: 50%; font-size: 19px; }.card-sync strong { display: block; font: 500 15px "DM Mono", monospace; letter-spacing: -.05em; }.card-sync strong span { margin-left: 2px; color: #86a4bd; font-size: 8px; }.card-sync small { display: block; margin-top: 2px; color: #8aa0b6; font-size: 7px; }.card-sync > b { align-self: start; margin-top: 1px; color: #43ad83; font: 6px "DM Mono", monospace; }

.hero-copy { position: relative; min-height: 730px; overflow: hidden; padding: 65px 62px 51px; color: #fff; background: #142b59; }.hero-copy::after { content: ''; position: absolute; width: 430px; height: 430px; right: -210px; bottom: -200px; border: 1px solid rgba(121, 194, 233, .15); border-radius: 50%; box-shadow: 0 0 0 28px rgba(121,194,233,.025), 0 0 0 58px rgba(121,194,233,.02); }.copy-index { position: absolute; top: 39px; right: 54px; color: #4c6c99; font: 10px "DM Mono", monospace; letter-spacing: .12em; }.copy-index span { color: #7895bb; }.copy-content { position: relative; z-index: 1; }.eyebrow { display: flex; align-items: center; gap: 9px; margin: 0; color: #79badb; font-size: 9px; }.eyebrow span { display: block; width: 24px; height: 1px; background: #38bdf2; }.hero-copy h1 { margin: 38px 0 23px; color: #fff; font-size: clamp(52px, 5.5vw, 78px); font-weight: 600; line-height: .99; letter-spacing: -.08em; }.hero-copy h1 em { color: #38bdf2; font-style: normal; }.hero-description { max-width: 360px; color: #a8bdd7; font-size: 14px; line-height: 1.9; }.capability-list { margin-top: 42px; border-top: 1px solid rgba(156, 191, 224, .22); }.capability-item { display: grid; grid-template-columns: 30px 1fr 18px; gap: 12px; align-items: start; padding: 15px 0; border-bottom: 1px solid rgba(156, 191, 224, .17); }.capability-index { color: #38bdf2; font: 9px "DM Mono", monospace; }.capability-item strong { display: block; font-size: 13px; font-weight: 600; letter-spacing: .04em; }.capability-item p { margin-top: 5px; color: #7e9abe; font-size: 10px; line-height: 1.5; }.capability-arrow { color: #7098c3; font-size: 14px; transition: color .2s, transform .2s; }.capability-item:hover .capability-arrow { color: #38bdf2; transform: translate(2px, -2px); }.copy-actions { display: flex; align-items: center; gap: 23px; margin-top: 38px; }.primary-action { display: inline-flex; align-items: center; gap: 25px; padding: 15px 17px 15px 19px; border: 1px solid #38bdf2; border-radius: 1px; color: #142b59; background: #38bdf2; font-size: 12px; font-weight: 700; cursor: pointer; transition: all .25s ease; }.primary-action b { display: grid; place-items: center; width: 22px; height: 22px; color: #38bdf2; background: #142b59; font-size: 14px; font-weight: 400; }.primary-action:hover { color: #fff; background: transparent; transform: translateY(-3px); }.primary-action:hover b { color: #142b59; background: #38bdf2; }.text-action { padding: 0; border: 0; color: #b4c8df; background: transparent; font-size: 11px; cursor: pointer; }.text-action span { margin-left: 8px; color: #38bdf2; transition: margin .2s; }.text-action:hover span { margin-left: 13px; }.copy-meta { display: flex; justify-content: space-between; margin-top: 55px; color: #55749f; font-size: 7px; }

.landing-footer { width: min(1380px, calc(100% - 88px)); margin: 0 auto; display: flex; justify-content: space-between; padding: 21px 0 27px; color: #93a8bd; font-size: 8px; }.footer-status { color: #55ae8a; }.footer-status i { margin-right: 5px; box-shadow: none; }.landing-footer b { margin-left: 6px; color: #2367c9; font-size: 13px; }

/* Readability pass: keep the control surface legible after the phone is tilted and scaled. */
.screen-heading small { color: #7caed0; font-size: 7px; }
.screen-heading strong { font-size: 24px; }
.twin-map { height: 228px; border-color: rgba(114, 182, 224, .42); background: linear-gradient(145deg, rgba(21,63,114,.92), rgba(9,30,70,.58)); box-shadow: inset 0 0 0 5px rgba(8,29,68,.15), 0 8px 18px rgba(4,21,53,.15); }
.map-grid { opacity: .46; background-size: 18px 18px; }
.map-topbar, .map-footer { position: absolute; z-index: 3; left: 10px; right: 10px; display: flex; justify-content: space-between; align-items: center; color: #8fc9e5; font: 6px "DM Mono", monospace; letter-spacing: .07em; }
.map-topbar { top: 9px; }.map-topbar span { color: #75dfb0; }.map-topbar i { display: inline-block; width: 4px; height: 4px; margin-right: 5px; border-radius: 50%; background: currentColor; }.map-topbar b, .map-footer b { color: #668fb5; font: inherit; font-weight: 400; }
.map-footer { bottom: 9px; color: #79a9c6; }.map-footer i { display: inline-block; width: 4px; height: 4px; margin-right: 5px; border-radius: 50%; color: #75dfb0; background: currentColor; }
.map-label { padding: 5px 7px; font-size: 7px; border: 1px solid rgba(127,200,235,.16); }.label-green { top: 34px; }.label-amber { top: 67px; }
.map-tooltip { bottom: 31px; padding-left: 9px; border-left: 2px solid #38bdf2; font-size: 7px; box-shadow: 0 6px 15px rgba(0,0,0,.22); }.map-tooltip b { font-size: 11px; }
.twin-map svg text { font-family: "DM Mono", monospace; }
.hero-description { color: #b7c9df; font-size: 15px; line-height: 1.85; }
.capability-list { border-top-color: rgba(156,191,224,.28); }
.capability-item { grid-template-columns: 34px 1fr 22px; gap: 13px; padding: 17px 0; border-bottom-color: rgba(156,191,224,.2); }
.capability-index { color: #4ac9f5; font-size: 11px; }
.capability-item strong { color: #fff; font-size: 16px; font-weight: 700; line-height: 1.25; }
.capability-item p { color: #91a8c7; font-size: 11px; line-height: 1.55; }
.capability-arrow { color: #83a9d2; font-size: 17px; }
.copy-actions { gap: 25px; }
.primary-action { min-height: 54px; padding: 14px 17px 14px 20px; font-size: 14px; font-weight: 800; }
.primary-action b { width: 24px; height: 24px; font-size: 15px; }
.text-action { min-height: 44px; color: #c0d0e2; font-size: 13px; font-weight: 600; }
.copy-meta { margin-top: 48px; color: #6683aa; font-size: 8px; }

@keyframes phone-enter { from { opacity: 0; transform: translate(-25px, 25px) rotate(-14deg); } to { opacity: 1; transform: translate(0, 0) rotate(-7deg); } }
@keyframes card-enter { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 1100px) {
  .landing-nav, .hero-frame, .landing-footer { width: min(100% - 42px, 900px); }
  .landing-nav { height: 76px; }
  .hero-frame { grid-template-columns: minmax(0, 1fr) minmax(355px, .82fr); }
  .hero-visual, .hero-copy { min-height: 650px; }
  .hero-copy { padding: 52px 42px 40px; }
  .phone-stage { left: 14%; top: 13%; width: 42%; }
  .phone-screen { min-height: 570px; padding: 18px 15px 14px; }
  .twin-map { height: 190px; }.screen-heading { margin-top: 21px; }.screen-heading strong { font-size: 18px; }
  .card-health { right: 7%; }.card-sync { right: 5%; }
  .hero-copy h1 { font-size: 56px; }
}

@media (max-width: 760px) {
  .landing-nav, .hero-frame, .landing-footer { width: calc(100% - 32px); }
  .nav-links a { display: none; }.nav-links { gap: 0; }.nav-console { padding: 10px 12px; }
  .hero-frame { display: block; box-shadow: none; }.hero-visual { min-height: 630px; }.hero-copy { min-height: auto; padding: 50px 28px 37px; }.hero-copy h1 { margin-top: 28px; font-size: clamp(52px, 14vw, 70px); }.copy-index { right: 28px; }.capability-list { margin-top: 33px; }.copy-actions { flex-wrap: wrap; margin-top: 30px; }.copy-meta { margin-top: 40px; }.landing-footer { gap: 12px; flex-wrap: wrap; line-height: 1.6; }.landing-footer > span:last-child { width: 100%; }
  .phone-stage { left: 12%; top: 10%; width: 48%; }.phone-screen { min-height: 555px; }.factory-ghost { width: 88%; left: 12%; top: 20%; }.card-health { top: 18%; right: 5%; width: 142px; }.card-sync { right: 5%; bottom: 18%; }.orbit-one { left: 2%; }.visual-ruler { left: 18px; right: 18px; }
}

@media (max-width: 460px) {
  .landing-nav { height: 70px; }.brand-lockup small { display: none; }.hero-visual { min-height: 570px; }.phone-stage { left: 9%; top: 14%; width: 56%; }.phone-screen { min-height: 500px; border-radius: 28px; padding: 16px 12px 13px; }.phone-device { padding: 7px; border-radius: 35px; }.phone-screen::before { border-radius: 29px; }.screen-nav { margin-top: 18px; }.screen-heading { margin-top: 20px; }.screen-heading strong { font-size: 16px; }.twin-map { height: 165px; margin-top: 15px; }.screen-metrics article { min-height: 75px; padding: 8px; }.screen-metrics strong { font-size: 17px; }.screen-metrics small { font-size: 5px; }.card-health { top: 11%; right: 3%; transform: scale(.84); transform-origin: top right; }.card-sync { bottom: 14%; right: 2%; transform: scale(.84); transform-origin: bottom right; }.factory-ghost { top: 23%; }.hero-copy { padding-inline: 22px; }.hero-copy h1 { font-size: 53px; }.primary-action { width: 100%; justify-content: space-between; }.text-action { margin-top: 2px; }.copy-meta { gap: 12px; flex-wrap: wrap; }.copy-meta span:last-child { margin-left: auto; }
}

@media (prefers-reduced-motion: reduce) {
  .phone-stage, .floating-card { animation: none; }
  .primary-action, .nav-console, .text-action span, .capability-arrow { transition: none; }
}
</style>