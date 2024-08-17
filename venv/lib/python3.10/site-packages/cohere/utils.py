import asyncio
import csv
import json
import time
import typing
from typing import Optional

import requests
from fastavro import parse_schema, reader, writer

from . import EmbedResponse, EmbedResponse_EmbeddingsFloats, EmbedResponse_EmbeddingsByType, ApiMeta, \
    EmbedByTypeResponseEmbeddings, ApiMetaBilledUnits, EmbedJob, CreateEmbedJobResponse, Dataset
from .datasets import DatasetsCreateResponse, DatasetsGetResponse


def get_terminal_states():
    return get_success_states() | get_failed_states()


def get_success_states():
    return {"complete", "validated"}


def get_failed_states():
    return {"unknown", "failed", "skipped", "cancelled", "failed"}


def get_id(
        awaitable: typing.Union[CreateEmbedJobResponse, DatasetsCreateResponse, EmbedJob, DatasetsGetResponse]):
    return getattr(awaitable, "job_id", None) or getattr(awaitable, "id", None) or getattr(
        getattr(awaitable, "dataset", None), "id", None)


def get_validation_status(awaitable: typing.Union[EmbedJob, DatasetsGetResponse]):
    return getattr(awaitable, "status", None) or getattr(getattr(awaitable, "dataset", None), "validation_status", None)


def get_job(cohere: typing.Any,
            awaitable: typing.Union[CreateEmbedJobResponse, DatasetsCreateResponse, EmbedJob, DatasetsGetResponse]) -> \
        typing.Union[
            EmbedJob, DatasetsGetResponse]:
    if awaitable.__class__.__name__ == "EmbedJob" or awaitable.__class__.__name__ == "CreateEmbedJobResponse":
        return cohere.embed_jobs.get(id=get_id(awaitable))
    elif awaitable.__class__.__name__ == "DatasetsGetResponse" or awaitable.__class__.__name__ == "DatasetsCreateResponse":
        return cohere.datasets.get(id=get_id(awaitable))
    else:
        raise ValueError(f"Unexpected awaitable type {awaitable}")


async def async_get_job(cohere: typing.Any, awaitable: typing.Union[CreateEmbedJobResponse, DatasetsCreateResponse]) -> \
        typing.Union[
            EmbedJob, DatasetsGetResponse]:
    if awaitable.__class__.__name__ == "EmbedJob" or awaitable.__class__.__name__ == "CreateEmbedJobResponse":
        return await cohere.embed_jobs.get(id=get_id(awaitable))
    elif awaitable.__class__.__name__ == "DatasetsGetResponse" or awaitable.__class__.__name__ == "DatasetsCreateResponse":
        return await cohere.datasets.get(id=get_id(awaitable))
    else:
        raise ValueError(f"Unexpected awaitable type {awaitable}")


def get_failure_reason(job: typing.Union[EmbedJob, DatasetsGetResponse]) -> Optional[str]:
    if isinstance(job, EmbedJob):
        return f"Embed job {job.job_id} failed with status {job.status}"
    elif isinstance(job, DatasetsGetResponse):
        return f"Dataset creation failed with status {job.dataset.validation_status} and error : {job.dataset.validation_error}"
    return None


@typing.overload
def wait(
        cohere: typing.Any,
        awaitable: CreateEmbedJobResponse,
        timeout: Optional[float] = None,
        interval: float = 10,
) -> EmbedJob:
    ...


@typing.overload
def wait(
        cohere: typing.Any,
        awaitable: DatasetsCreateResponse,
        timeout: Optional[float] = None,
        interval: float = 10,
) -> DatasetsGetResponse:
    ...


def wait(
        cohere: typing.Any,
        awaitable: typing.Union[CreateEmbedJobResponse, DatasetsCreateResponse],
        timeout: Optional[float] = None,
        interval: float = 2,
) -> typing.Union[EmbedJob, DatasetsGetResponse]:
    start_time = time.time()
    terminal_states = get_terminal_states()
    failed_states = get_failed_states()

    job = get_job(cohere, awaitable)
    while get_validation_status(job) not in terminal_states:
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(f"wait timed out after {timeout} seconds")

        time.sleep(interval)
        print("...")

        job = get_job(cohere, awaitable)

    if get_validation_status(job) in failed_states:
        raise Exception(get_failure_reason(job))

    return job


@typing.overload
async def async_wait(
        cohere: typing.Any,
        awaitable: CreateEmbedJobResponse,
        timeout: Optional[float] = None,
        interval: float = 10,
) -> EmbedJob:
    ...


@typing.overload
async def async_wait(
        cohere: typing.Any,
        awaitable: DatasetsCreateResponse,
        timeout: Optional[float] = None,
        interval: float = 10,
) -> DatasetsGetResponse:
    ...


async def async_wait(
        cohere: typing.Any,
        awaitable: typing.Union[CreateEmbedJobResponse, DatasetsCreateResponse],
        timeout: Optional[float] = None,
        interval: float = 10,
) -> typing.Union[EmbedJob, DatasetsGetResponse]:
    start_time = time.time()
    terminal_states = get_terminal_states()
    failed_states = get_failed_states()

    job = await async_get_job(cohere, awaitable)
    while get_validation_status(job) not in terminal_states:
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(f"wait timed out after {timeout} seconds")

        await asyncio.sleep(interval)
        print("...")

        job = await async_get_job(cohere, awaitable)

    if get_validation_status(job) in failed_states:
        raise Exception(get_failure_reason(job))

    return job


def sum_fields_if_not_none(obj: typing.Any, field: str) -> Optional[int]:
    non_none = [getattr(obj, field) for obj in obj if getattr(obj, field) is not None]
    return sum(non_none) if non_none else None


def merge_meta_field(metas: typing.List[ApiMeta]) -> ApiMeta:
    api_version = metas[0].api_version if metas else None
    billed_units = [meta.billed_units for meta in metas]
    input_tokens = sum_fields_if_not_none(billed_units, "input_tokens")
    output_tokens = sum_fields_if_not_none(billed_units, "output_tokens")
    search_units = sum_fields_if_not_none(billed_units, "search_units")
    classifications = sum_fields_if_not_none(billed_units, "classifications")
    warnings = {warning for meta in metas if meta.warnings for warning in meta.warnings}
    return ApiMeta(
        api_version=api_version,
        billed_units=ApiMetaBilledUnits(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            search_units=search_units,
            classifications=classifications
        ),
        warnings=list(warnings)
    )


def merge_embed_responses(responses: typing.List[EmbedResponse]) -> EmbedResponse:
    meta = merge_meta_field([response.meta for response in responses if response.meta])
    response_id = ", ".join(response.id for response in responses)
    texts = [
        text
        for response in responses
        for text in response.texts
    ]

    if responses[0].response_type == "embeddings_floats":
        embeddings_floats = typing.cast(typing.List[EmbedResponse_EmbeddingsFloats], responses)

        embeddings = [
            embedding
            for embeddings_floats in embeddings_floats
            for embedding in embeddings_floats.embeddings
        ]

        return EmbedResponse_EmbeddingsFloats(
            response_type="embeddings_floats",
            id=response_id,
            texts=texts,
            embeddings=embeddings,
            meta=meta
        )
    else:
        embeddings_type = typing.cast(typing.List[EmbedResponse_EmbeddingsByType], responses)

        embeddings_by_type = [
            response.embeddings
            for response in embeddings_type
        ]

        # only get set keys from the pydantic model (i.e. exclude fields that are set to 'None')
        fields = embeddings_type[0].embeddings.dict(exclude_unset=True).keys()

        merged_dicts = {
            field: [
                embedding
                for embedding_by_type in embeddings_by_type
                for embedding in getattr(embedding_by_type, field)
            ]
            for field in fields
        }

        embeddings_by_type_merged = EmbedByTypeResponseEmbeddings.parse_obj(merged_dicts)

        return EmbedResponse_EmbeddingsByType(
            response_type="embeddings_by_type",
            id=response_id,
            embeddings=embeddings_by_type_merged,
            texts=texts,
            meta=meta
        )


supported_formats = ["jsonl", "csv", "avro"]


def save_avro(dataset: Dataset, filepath: str):
    if not dataset.schema_:
        raise ValueError("Dataset does not have a schema")
    schema = parse_schema(json.loads(dataset.schema_))
    with open(filepath, "wb") as outfile:
        writer(outfile, schema, dataset_generator(dataset))


def save_jsonl(dataset: Dataset, filepath: str):
    with open(filepath, "w") as outfile:
        for data in dataset_generator(dataset):
            json.dump(data, outfile)
            outfile.write("\n")


def save_csv(dataset: Dataset, filepath: str):
    with open(filepath, "w") as outfile:
        for i, data in enumerate(dataset_generator(dataset)):
            if i == 0:
                writer = csv.DictWriter(outfile, fieldnames=list(data.keys()))
                writer.writeheader()
            writer.writerow(data)


def dataset_generator(dataset: Dataset):
    if not dataset.dataset_parts:
        raise ValueError("Dataset does not have dataset_parts")
    for part in dataset.dataset_parts:
        if not part.url:
            raise ValueError("Dataset part does not have a url")
        resp = requests.get(part.url, stream=True)
        for record in reader(resp.raw):
            yield record


class SdkUtils:

    @staticmethod
    def save_dataset(dataset: Dataset, filepath: str, format: typing.Literal["jsonl", "csv", "avro"] = "jsonl"):
        if format == "jsonl":
            return save_jsonl(dataset, filepath)
        if format == "csv":
            return save_csv(dataset, filepath)
        if format == "avro":
            return save_avro(dataset, filepath)
        raise Exception(f"unsupported format must be one of : {supported_formats}")


class SyncSdkUtils(SdkUtils):
    pass


class AsyncSdkUtils(SdkUtils):
    pass
