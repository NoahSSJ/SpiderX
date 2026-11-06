# 一个简易的分布式多站点爬虫

个人练手项目

## 依赖安装

最好linux部署，win似乎没有官方的redis服务。

```
conda activate your_env
pip install -r requirements.txt
```

## 测试
```
cd test
pytest
```

会检测一些api，纯算是否可以工作，mysql，redis，oss是否正常连接。

mysql，redis，oss需要自己在.env里配置

分布式日志可以使用阿里云SLS服务配置。