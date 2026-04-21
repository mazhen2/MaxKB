<template>
  <component
    :applicationAvailable="applicationAvailable"
    :is="currentTemplate"
    :application_profile="chatUser.application"
    :key="route.fullPath"
  />
</template>
<script setup lang="ts">
import { ref, computed, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import useStore from '@/stores'
import { useI18n } from 'vue-i18n'
const { locale } = useI18n({ useScope: 'global' })
const route = useRoute()
const { chatUser, common } = useStore()

const components: any = import.meta.glob('@/views/chat/**/index.vue', {
  eager: true,
})

const {
  params: { accessToken: routeAccessToken },
  query: { mode },
} = route as any

const currentTemplate = computed(() => {
  let modeName = ''
  if (chatUser.application) {
    if (!mode || mode === 'pc') {
      modeName = common.isMobile() ? 'mobile' : 'pc'
    } else {
      modeName = mode
    }
  } else {
    modeName = 'no-service'
  }

  return components[`/src/views/chat/${modeName}/index.vue`].default
})

const applicationAvailable = ref<boolean>(true)
onBeforeMount(async () => {
  locale.value = chatUser.getLanguage()
  if (routeAccessToken) {
    chatUser.setAccessToken(routeAccessToken as string)
  }

  if (!chatUser.application) {
    let authentication = false
    try {
      authentication = await chatUser.isAuthentication()
    } catch (e: any) {
      try {
        await chatUser.anonymousAuthentication()
      } catch (e2: any) {
        // ignore
      }
    }

    if (!authentication) {
      try {
        await chatUser.anonymousAuthentication()
      } catch (e: any) {
        // ignore
      }
    }

    if (!chatUser.application) {
      try {
        await chatUser.applicationProfile()
      } catch (e: any) {
        // ignore
      }
    }
  }
})
</script>
