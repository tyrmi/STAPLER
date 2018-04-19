import bayenv2
import bcftools
import bowtie2
import BWA
import Custom
import cutadapt
import FASTX_toolkit
import FastQC
import freebayes
import GATK
import misc
import Mosaik
import Picard
import PGU
import psmc
import samtools
import soap2
import tabix
import trimmomatic
import unix
import VCFtools


commands = {'CUSTOM':Custom.Custom,
            'bayenv2':bayenv2.bayenv2,
            'bcftools_call':bcftools.bcftools_call,
            'bcftools_mpileup':bcftools.bcftools_mpileup,
            'bgzip':tabix.bgzip,
            'bowtie2':bowtie2.bowtie2,
            'bwa_mem':BWA.bwa_mem,
            'bwa_bwasw':BWA.bwa_bwasw,
            'cutadapt':cutadapt.cutadapt,
            'fastx_toolkit_fasta_formatter':FASTX_toolkit.fasta_formatter,
            'fastx_toolkit_fasta_nucleotide_changer':FASTX_toolkit.fasta_nucleotide_changer,
            'fastx_toolkit_fastq_quality_boxplot_graph.sh':FASTX_toolkit.fastq_quality_boxplot_graph,
            'fastx_toolkit_fastq_quality_filter':FASTX_toolkit.fastq_quality_filter,
            'fastx_toolkit_fastq_quality_trimmer':FASTX_toolkit.fastq_quality_trimmer,
            'fastx_toolkit_fastq_to_fasta':FASTX_toolkit.fastq_to_fasta,
            'fastx_toolkit_fastx_artifacts_filter':FASTX_toolkit.fastx_artifacts_filter,
            'fastx_toolkit_fastx_clipper':FASTX_toolkit.fastx_clipper,
            'fastx_toolkit_fastx_collapser':FASTX_toolkit.fastx_collapser,
            'fastx_toolkit_fastx_nucleotide_distribution_graph.sh':FASTX_toolkit.fastx_nucleotide_distribution_graph,
            'fastx_toolkit_fastx_quality_stats':FASTX_toolkit.fastx_quality_stats,
            'fastx_toolkit_fastx_renamer':FASTX_toolkit.fastx_renamer,
            'fastx_toolkit_fastx_reverse_complement':FASTX_toolkit.fastx_reverse_complement,
            'fastx_toolkit_fastx_trimmer':FASTX_toolkit.fastx_trimmer,
            'fastqc':FastQC.fastqc,
            'freebayes':freebayes.freebayes,
            'psmc_fq2psmcfa':psmc.psmc_fq2psmcfa,
            'gatk_ApplyBQSR':GATK.ApplyBQSR,
            'gatk_BaseRecalibrator':GATK.BaseRecalibrator,
            'gatk_GenotypeGVCFs':GATK.GenotypeGVCFs,
            'gatk_HaplotypeCaller':GATK.HaplotypeCaller,
            'gatk_IndexFeatureFile':GATK.IndexFeatureFile,
            'psmc_history2ms':psmc.psmc_history2ms,
            'MosaikBuild':Mosaik.MosaikBuild,
            'MosaikAligner':Mosaik.MosaikAligner,
            'MosaikText':Mosaik.MosaikText,
            'PGU_vcf_allele_count_filter':PGU.PGU_vcf_allele_count_filter,
            'PGU_MAD_MAX':PGU.PGU_MAD_MAX,
            'PGU_ParalogAreaBEDmatic':PGU.PGU_ParalogAreaBEDmatic,
            'PGU_variant_density_filter':PGU.PGU_variant_density_filter,
            'PGU_vcf2fastq':PGU.PGU_vcf2fastq,
            'Picard_AddOrReplaceReadGroups':Picard.Picard_AddOrReplaceReadGroups,
            'Picard_CollectAlignmentSummaryMetrics':Picard.Picard_CollectAlignmentSummaryMetrics,
            'Picard_CollectInsertSizeMetrics': Picard.Picard_CollectInsertSizeMetrics,
            'Picard_CollectWgsMetrics':Picard.Picard_CollectWgsMetrics,
            'Picard_MarkDuplicates':Picard.Picard_MarkDuplicates,
            'Picard_SamFormatConverter':Picard.Picard_SamFormatConverter,
            'Picard_SortSam':Picard.Picard_SortSam,
            'psmc':psmc.psmc,
            'psmc_plot':psmc.psmc_plot,
            'psmc2history':psmc.psmc2history,
            'samtools_index':samtools.samtools_index,
            'samtools_rmdup':samtools.samtools_rmdup,
            'soap2':soap2.soap2,
            'tabix':tabix.tabix,
            'trimmomatic':trimmomatic.trimmomatic,
            'gzip':unix.gzip,
            'vcf_sort':misc.vcf_sort,
            'vcftools':VCFtools.VCFtools}
