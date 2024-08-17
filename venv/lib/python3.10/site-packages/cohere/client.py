import asyncio
import os
import typing
from concurrent.futures import ThreadPoolExecutor
from tokenizers import Tokenizer  # type: ignore

import httpx

from cohere.types.detokenize_response import DetokenizeResponse
from cohere.types.tokenize_response import TokenizeResponse

from . import EmbedResponse, EmbedInputType, EmbeddingType, EmbedRequestTruncate
from .base_client import BaseCohere, AsyncBaseCohere, OMIT
from .config import embed_batch_size
from .core import RequestOptions
from .environment import ClientEnvironment
from .manually_maintained.cache import CacheMixin
from .manually_maintained import tokenizers as local_tokenizers
from .overrides import run_overrides
from .utils import wait, async_wait, merge_embed_responses, SyncSdkUtils, AsyncSdkUtils

run_overrides()

# Use NoReturn as Never type for compatibility
Never = typing.NoReturn


def validate_args(obj: typing.Any, method_name: str, check_fn: typing.Callable[[typing.Any], typing.Any]) -> None:
    method = getattr(obj, method_name)

    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        check_fn(*args, **kwargs)
        return method(*args, **kwargs)

    setattr(obj, method_name, wrapped)


def throw_if_stream_is_true(*args, **kwargs) -> None:
    if kwargs.get("stream") is True:
        raise ValueError(
            "Since python sdk cohere==5.0.0, you must now use chat_stream(...) instead of chat(stream=True, ...)"
        )


def moved_function(fn_name: str, new_fn_name: str) -> typing.Any:
    """
    This method is moved. Please update usage.
    """

    def fn(*args, **kwargs):
        raise ValueError(
            f"Since python sdk cohere==5.0.0, the function {fn_name}(...) has been moved to {new_fn_name}(...). "
            f"Please update your code. Issues may be filed in https://github.com/cohere-ai/cohere-python/issues."
        )

    return fn


def deprecated_function(fn_name: str) -> typing.Any:
    """
    This method is deprecated. Please update usage.
    """

    def fn(*args, **kwargs):
        raise ValueError(
            f"Since python sdk cohere==5.0.0, the function {fn_name}(...) has been deprecated. "
            f"Please update your code. Issues may be filed in https://github.com/cohere-ai/cohere-python/issues."
        )

    return fn


class Client(BaseCohere, CacheMixin):
    def __init__(
        self,
        api_key: typing.Optional[typing.Union[str, typing.Callable[[], str]]] = None,
        *,
        base_url: typing.Optional[str] = os.getenv("CO_API_URL"),
        environment: ClientEnvironment = ClientEnvironment.PRODUCTION,
        client_name: typing.Optional[str] = None,
        timeout: typing.Optional[float] = None,
        httpx_client: typing.Optional[httpx.Client] = None,
    ):
        if api_key is None:
            api_key = _get_api_key_from_environment()

        BaseCohere.__init__(
            self,
            base_url=base_url,
            environment=environment,
            client_name=client_name,
            token=api_key,
            timeout=timeout,
            httpx_client=httpx_client,
        )

        validate_args(self, "chat", throw_if_stream_is_true)

    utils = SyncSdkUtils()

    # support context manager until Fern upstreams
    # https://linear.app/buildwithfern/issue/FER-1242/expose-a-context-manager-interface-or-the-http-client-easily
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._client_wrapper.httpx_client.httpx_client.close()

    wait = wait

    _executor = ThreadPoolExecutor(64)

    def embed(
        self,
        *,
        texts: typing.Sequence[str],
        model: typing.Optional[str] = OMIT,
        input_type: typing.Optional[EmbedInputType] = OMIT,
        embedding_types: typing.Optional[typing.Sequence[EmbeddingType]] = OMIT,
        truncate: typing.Optional[EmbedRequestTruncate] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
        batching: typing.Optional[bool] = True,
    ) -> EmbedResponse:
        if batching is False:
            return BaseCohere.embed(
                self,
                texts=texts,
                model=model,
                input_type=input_type,
                embedding_types=embedding_types,
                truncate=truncate,
                request_options=request_options,
            )

        texts_batches = [texts[i : i + embed_batch_size] for i in range(0, len(texts), embed_batch_size)]

        responses = [
            response
            for response in self._executor.map(
                lambda text_batch: BaseCohere.embed(
                    self,
                    texts=text_batch,
                    model=model,
                    input_type=input_type,
                    embedding_types=embedding_types,
                    truncate=truncate,
                    request_options=request_options,
                ),
                texts_batches,
            )
        ]

        return merge_embed_responses(responses)

    """
    The following methods have been moved or deprecated in cohere==5.0.0. Please update your usage.
    Issues may be filed in https://github.com/cohere-ai/cohere-python/issues.
    """
    check_api_key: Never = deprecated_function("check_api_key")
    loglikelihood: Never = deprecated_function("loglikelihood")
    batch_generate: Never = deprecated_function("batch_generate")
    codebook: Never = deprecated_function("codebook")
    batch_tokenize: Never = deprecated_function("batch_tokenize")
    batch_detokenize: Never = deprecated_function("batch_detokenize")
    detect_language: Never = deprecated_function("detect_language")
    generate_feedback: Never = deprecated_function("generate_feedback")
    generate_preference_feedback: Never = deprecated_function("generate_preference_feedback")
    create_dataset: Never = moved_function("create_dataset", ".datasets.create")
    get_dataset: Never = moved_function("get_dataset", ".datasets.get")
    list_datasets: Never = moved_function("list_datasets", ".datasets.list")
    delete_dataset: Never = moved_function("delete_dataset", ".datasets.delete")
    get_dataset_usage: Never = moved_function("get_dataset_usage", ".datasets.get_usage")
    wait_for_dataset: Never = moved_function("wait_for_dataset", ".wait")
    _check_response: Never = deprecated_function("_check_response")
    _request: Never = deprecated_function("_request")
    create_cluster_job: Never = deprecated_function("create_cluster_job")
    get_cluster_job: Never = deprecated_function("get_cluster_job")
    list_cluster_jobs: Never = deprecated_function("list_cluster_jobs")
    wait_for_cluster_job: Never = deprecated_function("wait_for_cluster_job")
    create_embed_job: Never = moved_function("create_embed_job", ".embed_jobs.create")
    list_embed_jobs: Never = moved_function("list_embed_jobs", ".embed_jobs.list")
    get_embed_job: Never = moved_function("get_embed_job", ".embed_jobs.get")
    cancel_embed_job: Never = moved_function("cancel_embed_job", ".embed_jobs.cancel")
    wait_for_embed_job: Never = moved_function("wait_for_embed_job", ".wait")
    create_custom_model: Never = deprecated_function("create_custom_model")
    wait_for_custom_model: Never = deprecated_function("wait_for_custom_model")
    _upload_dataset: Never = deprecated_function("_upload_dataset")
    _create_signed_url: Never = deprecated_function("_create_signed_url")
    get_custom_model: Never = deprecated_function("get_custom_model")
    get_custom_model_by_name: Never = deprecated_function("get_custom_model_by_name")
    get_custom_model_metrics: Never = deprecated_function("get_custom_model_metrics")
    list_custom_models: Never = deprecated_function("list_custom_models")
    create_connector: Never = moved_function("create_connector", ".connectors.create")
    update_connector: Never = moved_function("update_connector", ".connectors.update")
    get_connector: Never = moved_function("get_connector", ".connectors.get")
    list_connectors: Never = moved_function("list_connectors", ".connectors.list")
    delete_connector: Never = moved_function("delete_connector", ".connectors.delete")
    oauth_authorize_connector: Never = moved_function("oauth_authorize_connector", ".connectors.o_auth_authorize")

    def tokenize(
        self,
        *,
        text: str,
        model: str,
        request_options: typing.Optional[RequestOptions] = None,
        offline: bool = True,
    ) -> TokenizeResponse:
        # `offline` parameter controls whether to use an offline tokenizer. If set to True, the tokenizer config will be downloaded (and cached),
        # and the request will be processed using the offline tokenizer. If set to False, the request will be processed using the API. The default value is True.
        opts: RequestOptions = request_options or {}  # type: ignore

        if offline:
            try:
                tokens = local_tokenizers.local_tokenize(self, text=text, model=model)
                return TokenizeResponse(tokens=tokens, token_strings=[])
            except Exception:
                # Fallback to calling the API.
                opts["additional_headers"] = opts.get("additional_headers", {})
                opts["additional_headers"]["sdk-api-warning-message"] = "offline_tokenizer_failed"
        return super().tokenize(text=text, model=model, request_options=opts)

    def detokenize(
        self,
        *,
        tokens: typing.Sequence[int],
        model: str,
        request_options: typing.Optional[RequestOptions] = None,
        offline: typing.Optional[bool] = True,
    ) -> DetokenizeResponse:
        # `offline` parameter controls whether to use an offline tokenizer. If set to True, the tokenizer config will be downloaded (and cached),
        # and the request will be processed using the offline tokenizer. If set to False, the request will be processed using the API. The default value is True.
        opts: RequestOptions = request_options or {}  # type: ignore

        if offline:
            try:
                text = local_tokenizers.local_detokenize(self, model=model, tokens=tokens)
                return DetokenizeResponse(text=text)
            except Exception:
                # Fallback to calling the API.
                opts["additional_headers"] = opts.get("additional_headers", {})
                opts["additional_headers"]["sdk-api-warning-message"] = "offline_tokenizer_failed"

        return super().detokenize(tokens=tokens, model=model, request_options=opts)

    def fetch_tokenizer(self, *, model: str) -> Tokenizer:
        """
        Returns a Hugging Face tokenizer from a given model name.
        """
        return local_tokenizers.get_hf_tokenizer(self, model)


class AsyncClient(AsyncBaseCohere, CacheMixin):
    def __init__(
        self,
        api_key: typing.Optional[typing.Union[str, typing.Callable[[], str]]] = None,
        *,
        base_url: typing.Optional[str] = os.getenv("CO_API_URL"),
        environment: ClientEnvironment = ClientEnvironment.PRODUCTION,
        client_name: typing.Optional[str] = None,
        timeout: typing.Optional[float] = None,
        httpx_client: typing.Optional[httpx.AsyncClient] = None,
    ):
        if api_key is None:
            api_key = _get_api_key_from_environment()

        AsyncBaseCohere.__init__(
            self,
            base_url=base_url,
            environment=environment,
            client_name=client_name,
            token=api_key,
            timeout=timeout,
            httpx_client=httpx_client,
        )

        validate_args(self, "chat", throw_if_stream_is_true)

    utils = AsyncSdkUtils()

    # support context manager until Fern upstreams
    # https://linear.app/buildwithfern/issue/FER-1242/expose-a-context-manager-interface-or-the-http-client-easily
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._client_wrapper.httpx_client.httpx_client.aclose()

    wait = async_wait

    _executor = ThreadPoolExecutor(64)

    async def embed(
        self,
        *,
        texts: typing.Sequence[str],
        model: typing.Optional[str] = OMIT,
        input_type: typing.Optional[EmbedInputType] = OMIT,
        embedding_types: typing.Optional[typing.Sequence[EmbeddingType]] = OMIT,
        truncate: typing.Optional[EmbedRequestTruncate] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
        batching: typing.Optional[bool] = True,
    ) -> EmbedResponse:
        if batching is False:
            return await AsyncBaseCohere.embed(
                self,
                texts=texts,
                model=model,
                input_type=input_type,
                embedding_types=embedding_types,
                truncate=truncate,
                request_options=request_options,
            )

        texts_batches = [texts[i : i + embed_batch_size] for i in range(0, len(texts), embed_batch_size)]

        responses = typing.cast(
            typing.List[EmbedResponse],
            await asyncio.gather(
                *[
                    AsyncBaseCohere.embed(
                        self,
                        texts=text_batch,
                        model=model,
                        input_type=input_type,
                        embedding_types=embedding_types,
                        truncate=truncate,
                        request_options=request_options,
                    )
                    for text_batch in texts_batches
                ]
            ),
        )

        return merge_embed_responses(responses)

    """
    The following methods have been moved or deprecated in cohere==5.0.0. Please update your usage.
    Issues may be filed in https://github.com/cohere-ai/cohere-python/issues.
    """
    check_api_key: Never = deprecated_function("check_api_key")
    loglikelihood: Never = deprecated_function("loglikelihood")
    batch_generate: Never = deprecated_function("batch_generate")
    codebook: Never = deprecated_function("codebook")
    batch_tokenize: Never = deprecated_function("batch_tokenize")
    batch_detokenize: Never = deprecated_function("batch_detokenize")
    detect_language: Never = deprecated_function("detect_language")
    generate_feedback: Never = deprecated_function("generate_feedback")
    generate_preference_feedback: Never = deprecated_function("generate_preference_feedback")
    create_dataset: Never = moved_function("create_dataset", ".datasets.create")
    get_dataset: Never = moved_function("get_dataset", ".datasets.get")
    list_datasets: Never = moved_function("list_datasets", ".datasets.list")
    delete_dataset: Never = moved_function("delete_dataset", ".datasets.delete")
    get_dataset_usage: Never = moved_function("get_dataset_usage", ".datasets.get_usage")
    wait_for_dataset: Never = moved_function("wait_for_dataset", ".wait")
    _check_response: Never = deprecated_function("_check_response")
    _request: Never = deprecated_function("_request")
    create_cluster_job: Never = deprecated_function("create_cluster_job")
    get_cluster_job: Never = deprecated_function("get_cluster_job")
    list_cluster_jobs: Never = deprecated_function("list_cluster_jobs")
    wait_for_cluster_job: Never = deprecated_function("wait_for_cluster_job")
    create_embed_job: Never = moved_function("create_embed_job", ".embed_jobs.create")
    list_embed_jobs: Never = moved_function("list_embed_jobs", ".embed_jobs.list")
    get_embed_job: Never = moved_function("get_embed_job", ".embed_jobs.get")
    cancel_embed_job: Never = moved_function("cancel_embed_job", ".embed_jobs.cancel")
    wait_for_embed_job: Never = moved_function("wait_for_embed_job", ".wait")
    create_custom_model: Never = deprecated_function("create_custom_model")
    wait_for_custom_model: Never = deprecated_function("wait_for_custom_model")
    _upload_dataset: Never = deprecated_function("_upload_dataset")
    _create_signed_url: Never = deprecated_function("_create_signed_url")
    get_custom_model: Never = deprecated_function("get_custom_model")
    get_custom_model_by_name: Never = deprecated_function("get_custom_model_by_name")
    get_custom_model_metrics: Never = deprecated_function("get_custom_model_metrics")
    list_custom_models: Never = deprecated_function("list_custom_models")
    create_connector: Never = moved_function("create_connector", ".connectors.create")
    update_connector: Never = moved_function("update_connector", ".connectors.update")
    get_connector: Never = moved_function("get_connector", ".connectors.get")
    list_connectors: Never = moved_function("list_connectors", ".connectors.list")
    delete_connector: Never = moved_function("delete_connector", ".connectors.delete")
    oauth_authorize_connector: Never = moved_function("oauth_authorize_connector", ".connectors.o_auth_authorize")

    async def tokenize(
        self,
        *,
        text: str,
        model: str,
        request_options: typing.Optional[RequestOptions] = None,
        offline: typing.Optional[bool] = True,
    ) -> TokenizeResponse:
        # `offline` parameter controls whether to use an offline tokenizer. If set to True, the tokenizer config will be downloaded (and cached),
        # and the request will be processed using the offline tokenizer. If set to False, the request will be processed using the API. The default value is True.
        opts: RequestOptions = request_options or {}  # type: ignore
        if offline:
            try:
                tokens = await local_tokenizers.async_local_tokenize(self, model=model, text=text)
                return TokenizeResponse(tokens=tokens, token_strings=[])
            except Exception:
                opts["additional_headers"] = opts.get("additional_headers", {})
                opts["additional_headers"]["sdk-api-warning-message"] = "offline_tokenizer_failed"

        return await super().tokenize(text=text, model=model, request_options=opts)

    async def detokenize(
        self,
        *,
        tokens: typing.Sequence[int],
        model: str,
        request_options: typing.Optional[RequestOptions] = None,
        offline: typing.Optional[bool] = True,
    ) -> DetokenizeResponse:
        # `offline` parameter controls whether to use an offline tokenizer. If set to True, the tokenizer config will be downloaded (and cached),
        # and the request will be processed using the offline tokenizer. If set to False, the request will be processed using the API. The default value is True.
        opts: RequestOptions = request_options or {}  # type: ignore
        if offline:
            try:
                text = await local_tokenizers.async_local_detokenize(self, model=model, tokens=tokens)
                return DetokenizeResponse(text=text)
            except Exception:
                opts["additional_headers"] = opts.get("additional_headers", {})
                opts["additional_headers"]["sdk-api-warning-message"] = "offline_tokenizer_failed"

        return await super().detokenize(tokens=tokens, model=model, request_options=opts)

    async def fetch_tokenizer(self, *, model: str) -> Tokenizer:
        """
        Returns a Hugging Face tokenizer from a given model name.
        """
        return await local_tokenizers.async_get_hf_tokenizer(self, model)


def _get_api_key_from_environment() -> typing.Optional[str]:
    """
    Retrieves the Cohere API key from specific environment variables.
    CO_API_KEY is preferred (and documented) COHERE_API_KEY is accepted (but not documented).
    """
    return os.getenv("CO_API_KEY", os.getenv("COHERE_API_KEY"))
