/** Auth feature user-visible copy and validation messages. */

export const authCopy = {
  pageBadge: "账号",
  pageTitle: "登录 / 注册",
  pageDescription: "使用邮箱验证码登录，首次登录将自动注册",
  emailLabel: "邮箱",
  emailPlaceholder: "you@example.com",
  emailCodeLabel: "邮箱验证码",
  emailCodePlaceholder: "6 位数字",
  codeSentHint: "验证码已发送，请查收邮件",
  sendCode: "获取验证码",
  resendCode: "重新发送",
  sendingCode: "发送中...",
  submit: "登录 / 注册",
  submitting: "登录中...",
} as const;

export const authValidation = {
  emailRequired: "请输入邮箱",
  emailCodeRequired: "请输入邮箱验证码",
} as const;

export const authErrors = {
  sendCodeFailed: "发送验证码失败",
  loginFailed: "登录失败",
} as const;
