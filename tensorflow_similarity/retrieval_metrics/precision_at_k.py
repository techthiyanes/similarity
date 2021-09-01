import tensorflow as tf

from .retrieval_metric import RetrievalMetric
from tensorflow_similarity.types import FloatTensor, IntTensor, BoolTensor


class PrecisionAtK(RetrievalMetric):
    r"""Precision@K is computed as.

                         k
                        ===
                        \    rel
                        /       ij
              TP        ===
                i      j = 1
    P @k = --------- = -----------
     i     TP  + FP         k
             i     i

    Where: K is the number of neighbors in the i_th query result set.
           rel is the relevance mask (indicator function) for the i_th query.
           i represents the i_th query.
           j represents the j_th ranked query result.

    P@K is unordered and does not take into account the rank of the TP results.

    This metric is useful when we are interested in evaluating the embedding
    within the context of a kNN classifier or as part of a clustering method.

    Attributes:
        name: Name associated with the metric object, e.g., precision@5

        canonical_name: The canonical name associated with metric,
        e.g., precision@K

        k: The number of nearest neighbors over which the metric is computed.

        distance_threshold: The max distance below which a nearest neighbor is
        considered a valid match.

        average: {'micro', 'macro'} Determines the type of averaging performed
        on the data.

            'micro': Calculates metrics globally over all data.

            'macro': Calculates metrics for each label and takes the unweighted
                     mean.
    """
    def __init__(self,
                 name: str = 'precision',
                 k: int = 1,
                 **kwargs) -> None:
        if 'canonical_name' not in kwargs:
            kwargs['canonical_name'] = 'precision@k'

        super().__init__(name=name, k=k, **kwargs)

    def compute(self,
                *,
                query_labels: IntTensor,
                match_mask: BoolTensor,
                **kwargs) -> FloatTensor:
        """Compute the metric

        Args:
            query_labels: A 1D array of the labels associated with the
            embedding queries.

            match_mask: A 2D mask where a 1 indicates a match between the
            jth query and the kth neighbor and a 0 indicates a mismatch.

            **kwargs: Additional compute args.

        Returns:
            metric results.
        """
        k_slice = tf.cast(match_mask[:, :self.k], dtype='float')
        tp = tf.math.reduce_sum(k_slice, axis=1)
        per_example_p = tf.math.divide(tp, self.k)

        if self.average == 'micro':
            p_at_k = tf.math.reduce_mean(per_example_p)
        elif self.average == 'macro':
            per_class_metrics = 0
            class_labels = tf.unique(query_labels)[0]
            for label in class_labels:
                idxs = tf.where(query_labels == label)
                c_slice = tf.gather(per_example_p, indices=idxs)
                per_class_metrics += tf.math.reduce_mean(c_slice)
            p_at_k = tf.math.divide(per_class_metrics, len(class_labels))
        else:
            raise ValueError(f'{self.average} is not a supported average '
                             'option')
        result: FloatTensor = p_at_k
        return result