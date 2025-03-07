__all__ = ['process_pc_neighborhood', 'process_pc_pathsbetween',
           'process_pc_pathsfromto', 'process_owl', 'process_owl_str',
           'process_owl_gz', 'process_model']

import itertools
from pybiopax import model_from_owl_file, model_from_owl_str, \
    model_from_pc_query, model_from_owl_gz
from .processor import BiopaxProcessor

default_databases = ['wp', 'smpdb', 'reconx', 'reactome', 'psp', 'pid',
                     'panther', 'netpath', 'msigdb', 'mirtarbase', 'kegg',
                     'intact', 'inoh', 'humancyc', 'hprd',
                     'drugbank', 'dip', 'corum']


def process_pc_neighborhood(gene_names, neighbor_limit=1,
                            database_filter=None):
    """Returns a BiopaxProcessor for a PathwayCommons neighborhood query.

    The neighborhood query finds the neighborhood around a set of source genes.

    http://www.pathwaycommons.org/pc2/#graph

    http://www.pathwaycommons.org/pc2/#graph_kind

    Parameters
    ----------
    gene_names : list
        A list of HGNC gene symbols to search the neighborhood of.
        Examples: ['BRAF'], ['BRAF', 'MAP2K1']
    neighbor_limit : Optional[int]
        The number of steps to limit the size of the neighborhood around
        the gene names being queried. Default: 1
    database_filter : Optional[list]
        A list of database identifiers to which the query is restricted.
        Examples: ['reactome'], ['biogrid', 'pid', 'psp']
        If not given, all databases are used in the query. For a full
        list of databases see http://www.pathwaycommons.org/pc2/datasources

    Returns
    -------
    BiopaxProcessor
        A BiopaxProcessor containing the obtained BioPAX model in its model
        attribute and a list of extracted INDRA Statements from the model in
        its statements attribute.
    """
    model = model_from_pc_query('neighborhood', source=gene_names,
                                limit=neighbor_limit,
                                datasource=database_filter)
    if model is not None:
        return process_model(model)


def process_pc_pathsbetween(gene_names, neighbor_limit=1,
                            database_filter=None, block_size=None):
    """Returns a BiopaxProcessor for a PathwayCommons paths-between query.

    The paths-between query finds the paths between a set of genes. Here
    source gene names are given in a single list and all directions of paths
    between these genes are considered.

    http://www.pathwaycommons.org/pc2/#graph

    http://www.pathwaycommons.org/pc2/#graph_kind

    Parameters
    ----------
    gene_names : list
        A list of HGNC gene symbols to search for paths between.
        Examples: ['BRAF', 'MAP2K1']
    neighbor_limit : Optional[int]
        The number of steps to limit the length of the paths between
        the gene names being queried. Default: 1
    database_filter : Optional[list]
        A list of database identifiers to which the query is restricted.
        Examples: ['reactome'], ['biogrid', 'pid', 'psp']
        If not given, all databases are used in the query. For a full
        list of databases see http://www.pathwaycommons.org/pc2/datasources
    block_size : Optional[int]
        Large paths-between queries (above ~60 genes) can error on the server
        side. In this case, the query can be replaced by a series of
        smaller paths-between and paths-from-to queries each of which contains
        block_size genes.

    Returns
    -------
    bp : BiopaxProcessor
        A BiopaxProcessor containing the obtained BioPAX model in bp.model.
    """
    if not block_size:
        model = model_from_pc_query('pathsbetween',
                                    source=gene_names,
                                    limit=neighbor_limit,
                                    datasource=database_filter)

        if model is not None:
            return process_model(model)
    else:
        gene_blocks = [gene_names[i:i + block_size] for i in
                       range(0, len(gene_names), block_size)]
        stmts = []
        # Run pathsfromto between pairs of blocks and pathsbetween
        # within each block. This breaks up a single call with N genes into
        # (N/block_size)*(N/blocksize) calls with block_size genes
        for genes1, genes2 in itertools.product(gene_blocks, repeat=2):
            if genes1 == genes2:
                bp = process_pc_pathsbetween(genes1,
                                             database_filter=database_filter,
                                             block_size=None)
            else:
                bp = process_pc_pathsfromto(genes1, genes2,
                                            database_filter=database_filter)
            stmts += bp.statements


def process_pc_pathsfromto(source_genes, target_genes, neighbor_limit=1,
                           database_filter=None):
    """Returns a BiopaxProcessor for a PathwayCommons paths-from-to query.

    The paths-from-to query finds the paths from a set of source genes to
    a set of target genes.

    http://www.pathwaycommons.org/pc2/#graph

    http://www.pathwaycommons.org/pc2/#graph_kind

    Parameters
    ----------
    source_genes : list
        A list of HGNC gene symbols that are the sources of paths being
        searched for.
        Examples: ['BRAF', 'RAF1', 'ARAF']
    target_genes : list
        A list of HGNC gene symbols that are the targets of paths being
        searched for.
        Examples: ['MAP2K1', 'MAP2K2']
    neighbor_limit : Optional[int]
        The number of steps to limit the length of the paths
        between the source genes and target genes being queried. Default: 1
    database_filter : Optional[list]
        A list of database identifiers to which the query is restricted.
        Examples: ['reactome'], ['biogrid', 'pid', 'psp']
        If not given, all databases are used in the query. For a full
        list of databases see http://www.pathwaycommons.org/pc2/datasources

    Returns
    -------
    bp : BiopaxProcessor
        A BiopaxProcessor containing the obtained BioPAX model in bp.model.
    """
    model = model_from_pc_query('pathsfromto',
                                source=source_genes,
                                target=target_genes,
                                limit=neighbor_limit,
                                datasource=database_filter)
    if model is not None:
        return process_model(model)


def process_owl(owl_filename, encoding=None):
    """Returns a BiopaxProcessor for a BioPAX OWL file.

    Parameters
    ----------
    owl_filename : str
        The name of the OWL file to process.
    encoding : Optional[str]
        The encoding type to be passed to :func:`pybiopax.model_from_owl_file`.

    Returns
    -------
    bp : BiopaxProcessor
        A BiopaxProcessor containing the obtained BioPAX model in bp.model.
    """
    model = model_from_owl_file(owl_filename, encoding=encoding)
    return process_model(model)


def process_owl_gz(owl_gz_filename):
    """Returns a BiopaxProcessor for a gzipped BioPAX OWL file.

    Parameters
    ----------
    owl_gz_filename : str
        The name of the gzipped OWL file to process.

    Returns
    -------
    bp : BiopaxProcessor
        A BiopaxProcessor containing the obtained BioPAX model in bp.model.
    """
    model = model_from_owl_gz(owl_gz_filename)
    return process_model(model)


def process_owl_str(owl_str):
    """Returns a BiopaxProcessor for a BioPAX OWL file.

    Parameters
    ----------
    owl_str : str
        The string content of an OWL file to process.

    Returns
    -------
    bp : BiopaxProcessor
        A BiopaxProcessor containing the obtained BioPAX model in bp.model.
    """
    model = model_from_owl_str(owl_str)
    return process_model(model)


def process_model(model):
    """Returns a BiopaxProcessor for a BioPAX model object.

    Parameters
    ----------
    model : org.biopax.paxtools.model.Model
        A BioPAX model object.

    Returns
    -------
    bp : BiopaxProcessor
        A BiopaxProcessor containing the obtained BioPAX model in bp.model.
    """
    bp = BiopaxProcessor(model)
    bp.process_all()
    return bp
