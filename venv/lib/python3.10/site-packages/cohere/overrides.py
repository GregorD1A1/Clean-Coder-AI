from . import EmbedByTypeResponseEmbeddings


def allow_access_to_aliases(self, name):
    for field_name, field_info in self.__fields__.items():
        if field_info.alias == name:
            return getattr(self, field_name)
    raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'")


def run_overrides():
    """
        These are overrides to allow us to make changes to generated code without touching the generated files themselves.
        Should be used judiciously!
    """

    # Override to allow access to aliases in EmbedByTypeResponseEmbeddings eg embeddings.float rather than embeddings.float_
    setattr(EmbedByTypeResponseEmbeddings, "__getattr__", allow_access_to_aliases)
