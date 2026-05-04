# easyScholar Rank Fields

`easyscholar-rank` calls:

```text
GET https://www.easyscholar.cc/open/getPublicationRank?secretKey=<KEY>&publicationName=<刊名>
```

The live API returns `code`, `msg`, and `data`. `data.customRank` carries user-defined rank groups when configured. `data.officialRank` is the authoritative profile object and currently contains `all` plus `select` views.

## Field Map

The adapter keeps the raw `officialRank` object intact and adds normalized label detection. Known fields and aliases:

| Canonical label | Common API keys / Chinese labels | Meaning |
|---|---|---|
| `pku` | `pku`, `北大核心`, `北京大学核心` | PKU Chinese Core Journal catalog |
| `cssci` | `cssci`, `南大核心`, `南京大学核心` | CSSCI source / extended source labels |
| `cscd` | `cscd`, `中国科学引文数据库` | Chinese Science Citation Database labels |
| `cstpcd` | `cstpcd`, `中国科技核心`, `科技核心` | CSTPCD / China S&T core labels |
| `ami` | `ami`, `人大复印`, `a刊` | AMI and related social-science labels |
| `fms` | `fms`, `管理科学高质量期刊` | FMS management-science labels |
| `sci` | `sci`, `scie` | SCI / SCIE labels when present |
| `ssci` | `ssci` | SSCI labels when present |
| `ei` | `ei` | Engineering Index label when present |
| `ahci` | `ahci` | AHCI label when present |

## Output Contract

```json
{
  "query": "经济研究",
  "status": "ok",
  "code": 200,
  "rank_profile": {
    "customRank": {},
    "officialRank": {"all": {}, "select": {}},
    "field_count": 37,
    "catalog_labels_detected": {
      "pku": true,
      "cssci": true,
      "cscd": false,
      "cstpcd": false
    }
  }
}
```

The adapter treats all rank labels as `trust_level=rank-cn`. It never writes the API key to disk; key lookup order is env `EASYSCHOLAR_SECRET_KEY` then macOS Keychain service `easyscholar`.
