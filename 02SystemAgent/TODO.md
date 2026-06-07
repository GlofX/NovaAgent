# TODO: 优化滑动窗口截断逻辑，使用Token-aware
# TODO: 反思逻辑会导致 死循环,加反思次数限制


# 可优化：action 白名单

# NOTICE:没有 Observation 截断（高危）
# NOTICE:'Observation 塞回 history 的方式不标准',OpenAI 官方 tool 格式