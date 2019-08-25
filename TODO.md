# 要进行哪些完善？

## 脚本

- unpackbootimg：用谷歌最新的mkbootimg取代（这是个Python脚本）
- 用户应当项目放在Android源码根目录，本工具通过检测`.repo`目录来判断是否在Android源码目录下。
  - 当然也可脱离Android源码树运行，但你必须手动指定源码树路径。
- 通过判断内核的架构，来自动更改BoardConfig.mk.template中的架构配置
- 用户需要指定ROM的类型。
  - 将ROM的专属配置文件归到一个专门的目录中，按需提取，并相应地更改AndroidProducts.mk
- 连接手机以检测几个主要分区的大小，然后更新BoardConfig.mk.template
- **可能要考虑用Python重写！**

## 模板

- 加入TWRP的参数选项
