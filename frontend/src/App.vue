<template>
  <router-view />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

html, body, #app {
  height: 100%;
}

body {
  min-width: 320px;
  background: #f3f6fa;
}

button,
a {
  -webkit-tap-highlight-color: transparent;
}
</style>