# Blog

This repository contains the source for my blog site at [https://stephankoe.github.io/blog](https://stephankoe.github.io/blog). This blog is built with [Hugo](https://gohugo.io/) and the theme [Stack](https://themes.gohugo.io/themes/hugo-theme-stack). 

## Serve locally

Hugo allows to easily serve blog sites locally with the `hugo serve` command. However, some pages make use of Pandoc-style citation syntax that Hugo's [goldmark](https://github.com/yuin/goldmark) Markdown parser currently doesn't support. Therefore, the [markdown preprocessor toolkit](https://github.com/stephankoe/markdown-preprocessor) is needed to parse Pandoc-style citations with HTML. So, to serve this blog locally, run the following commands from this repository's root directory:

```bash
find content/post -type f -iname '*.md' -exec preprocess-citations -i --bibliography=assets/bibliography.json {} \;
hugo serve -D
```