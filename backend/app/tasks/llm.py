from typing import Literal

import instructor
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from app.config import settings


SYSTEM_PROMPT = """1、你是一个公司合同信息提取专家，只能帮我提取合同内容的信息，**绝对不可以加入任何主观分析和判断**。
2、我方集团下包括的公司有："艾德韦宣","艾迪霖杰","愿景艾德","范思广告","设计周"。
请按照要求提取合同内的信息，如果某项信息未找到，请回答"未找到"。"""


ContractType = Literal[
    "承揽合同",
    "运输合同",
    "租赁合同",
    "财产保险合同",
    "押金合同",
    "租赁合同（含押金）",
]


class ContractInfo(BaseModel):
    """合同关键字段抽取结果。所有字段必填，未找到一律填\"未找到\"。"""

    合同类型: ContractType = Field(
        ...,
        description=(
            "请从五种类型中判断：承揽合同, 运输合同, 租赁合同, 财产保险合同, 押金合同。"
            "如若合同中只有押金没有其他付款需求则为押金合同；如果有则写为：租赁合同（含押金）。"
            "如有酒店住宿、订房、晚宴，则写为承揽合同。如果不属于以上，则归类为承揽合同。"
        ),
    )
    合同名称: str = Field(
        ...,
        description=(
            "把提供某某服务中的\"某某服务\"作为合同名称，且最后命名以\"合同\"两字结尾。经甲乙双方协商确定，甲方委托乙方提供[xx]服务，则文件名为xx服务合同"
            "如有判断为：保密、终止、补充协议，需括号提示（xx协议）（不是文档标题）。"
        ),
    )
    合作方: str = Field(
        ...,
        description=(
            "1.必须提取合同中除我方公司（本公司）所扮演角色（如甲方/乙方/丙方等）对应的名称以外的所有签约主体名称。"
            "2.签约主体类型包括但不限于：公司、事务所、学校、机构、行政单位或自然人。"
            "【高优先级覆盖规则】如果合同内容中明确出现\"实际付款对象某某公司\"或\"由某某公司代付\"等描述，"
            "则该实际付款或代付的\"某某公司\"（仅限公司）必须被提取为唯一的合作方。"
            "3.【无付款描述时适用】双边协议提取唯一签约主体；多方协议必须列出所有非我方公司的签约主体。"
            "4.多个合作方之间必须且仅能使用英文逗号加一个空格分隔。"
            "5.【禁止】包含我方公司名称。"
            "6.如果甲乙双方都是我方公司名称，则提取乙方公司名称为合作方。"
        ),
    )
    甲方公司: str = Field(
        ...,
        description=(
            "强制覆盖逻辑：1.唯一信息来源是合同中涉及款项支付或收取的条款。"
            "2.甲方公司必须是合同项下款项的支付义务方（Payer）。"
            "如果支付是由其关联公司、搭建公司或供应商代付，该支付义务方仍视作甲方。"
            "如果没有支付信息，就以合同中甲方作为甲方公司。"
        ),
    )
    乙方公司: str = Field(
        ...,
        description=(
            "强制覆盖逻辑：1.唯一信息来源是合同中涉及款项支付或收取的条款。"
            "2.乙方公司必须是合同项下款项的最终接收方/收款方（Payee/Recipient）。"
            "如果没有支付信息，就以合同中乙方作为乙方公司。"
        ),
    )
    合同年度: str = Field(
        ...,
        description=(
            "查找以SRQ、SEQ、SWQ、SPQ或SDQ开头的项目编号，取第四位和第五位作为年份，前面补上20，"
            "结果为4位纯数字。如果没有找到则写：未找到。"
        ),
    )
    项目编号: str = Field(
        ...,
        description="查找以SRQ、SEQ、SWQ、SPQ或SDQ开头的项目编号，如果没有找到则写：未找到。",
    )
    合同金额: str = Field(
        ...,
        description=(
            "强制提取第一个出现的金额数字，格式化为 xxx,xxx.xx（如134500元格式化为134,500.00）。"
            "如果合同名称里面包含\"保密协议\"，则填\"未找到\"。"
        ),
    )
    合同币种: str = Field(
        ...,
        description="币种类型，统一格式为[币种]（如人民币记录为[RMB]，美元记录为[USD]等）。如合同中没有体现币种，则记录为[RMB]。",
    )
    合同期限: str = Field(
        ...,
        description="合同的有效期限或服务起止时间。如未找到则填\"未找到\"。",
    )
    违约金额比例: str = Field(
        ...,
        alias="违约金额/比例",
        description="违约金的具体金额或比例。如未找到则填\"未找到\"。",
    )
    审计条款: str = Field(
        ...,
        description="合同中关于审计相关的条款描述。如未找到则填\"未找到\"。",
    )

    model_config = {"populate_by_name": True}


_client = instructor.from_openai(
    OpenAI(
        base_url=f"{settings.ollama_url.rstrip('/')}/v1",
        api_key="ollama",  # Ollama 不校验，占位即可
    ),
    mode=instructor.Mode.JSON,
)


def extract_fields(text: str) -> dict:
    if not settings.ollama_url:
        raise RuntimeError("OLLAMA_URL 未配置")

    user_prompt = f"合同内容：\n{text}"
    logger.info(
        "[LLM] model={} prompt_len={} preview={}",
        settings.llm_model,
        len(user_prompt),
        user_prompt[:300].replace("\n", " "),
    )

    try:
        obj, raw = _client.chat.completions.create_with_completion(
            model=settings.llm_model,
            response_model=ContractInfo,
            max_retries=3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=4096,
            # Ollama 专属：禁用 Qwen3 的 <think> 推理，避免 token 被思考过程吃光
            extra_body={"think": False, "options": {"num_ctx": 16384}},
        )
    except ValidationError as e:
        logger.error("[LLM] 校验失败已用尽重试: {}", e)
        raise

    logger.info(
        "[LLM] done finish_reason={} content={}",
        raw.choices[0].finish_reason if raw.choices else "?",
        obj.model_dump(by_alias=True),
    )

    data = obj.model_dump(by_alias=True)
    data["项目序号"] = ""  # 人工字段
    return data
