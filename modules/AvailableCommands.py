import ANGSD
import bedtools
import BLAST
import bayenv2
import bowtie2
import BWA
import Custom
import FASTX_toolkit
import FastQC
import freebayes
import Mosaik
import novoalign
import Picard
import samtools
import tabix
import Trimmomatic
import vcflib
import VCFtools


commands = {'ANGSD': ANGSD.ANGSD,
            'ANY_TOOL':Custom.ANY_TOOL,
            'baitron':Custom.baitron,
            'baits_from_blast_selectomatic':Custom.baits_from_blast_selectomatic,
            'bayenv2':bayenv2.bayenv2,
            'bedtools_coverageBed':bedtools.bedtools_coverageBed,
            'bedtools_multiBamCov':bedtools.bedtools_multiBamCov,
            'bgzip':tabix.bgzip,
            'blast':BLAST.blast,
            'bowtie2':bowtie2.bowtie2,
            'bwa_mem':BWA.BWA_MEM,
            'fastq_to_fasta':FASTX_toolkit.fastq_to_fasta,
            'fastx_quality_stats':FASTX_toolkit.fastx_quality_stats,
            'fastq_quality_boxplot_graph':FASTX_toolkit.fastq_quality_boxplot_graph,
            'fastq_quality_trimmer':FASTX_toolkit.fastq_quality_trimmer,
            'fastx_nucleotide_distribution_graph':FASTX_toolkit.fastx_nucleotide_distribution_graph,
            'fastx_trimmer':FASTX_toolkit.fastx_trimmer,
            'fastq_quality_filter':FASTX_toolkit.fastq_quality_filter,
            'fastqc':FastQC.fastqc,
            'freebayes':freebayes.freebayes,
            'freebayes_parallel':freebayes.freebayes_parallel,
            'MAD_MAX':Custom.MAD_MAX,
            'MosaikBuild':Mosaik.MosaikBuild,
            'MosaikAligner':Mosaik.MosaikAligner,
            'MosaikText':Mosaik.MosaikText,
            'novoalign':novoalign.novoalign,
            'ParalogAreaBEDmatic':Custom.ParalogAreaBEDmatic,
            'Picard_AddOrReplaceReadGroups':Picard.Picard_AddOrReplaceReadGroups,
            'Picard_CollectAlignmentSummaryMetrics':Picard.Picard_CollectAlignmentSummaryMetrics,
            'Picard_CollectAlignmentSummaryMetrics_1.128':Picard.Picard_CollectAlignmentSummaryMetrics_1128,
            'Picard_CollectInsertSizeMetrics': Picard.Picard_CollectInsertSizeMetrics,
            'Picard_CollectWgsMetrics':Picard.Picard_CollectWgsMetrics,
            'Picard_CompareSAMs':Picard.Picard_CompareSAMs,
            'Picard_MarkDuplicates':Picard.Picard_MarkDuplicates,
            'Picard_MergeSamFiles':Picard.Picard_MergeSamFiles,
            'Picard_SamFormatConverter':Picard.Picard_SamFormatConverter,
            'Picard_SortSam':Picard.Picard_SortSam,
            'samtools_index':samtools.samtools_index,
            'samtools_rmdup':samtools.samtools_rmdup,
            'tabix':tabix.tabix,
            'Trimmomatic':Trimmomatic.Trimmomatic,
            'variant_density_filter':Custom.variant_density_filter,
            'vcflib_vcfallelicprimitives':vcflib.vcflib_vcfallelicprimitives,
            'vcftools':VCFtools.VCFtools}
