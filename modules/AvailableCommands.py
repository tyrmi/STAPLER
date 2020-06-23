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
            'CUSTOM_NO_OUTPUT':Custom.Custom_no_output,
            'stapler_bayenv2':bayenv2.bayenv2,
            'stapler_bcftools_call':bcftools.bcftools_call,
            'stapler_bcftools_mpileup':bcftools.bcftools_mpileup,
            'stapler_bgzip':tabix.bgzip,
            'stapler_bowtie2':bowtie2.bowtie2,
            'stapler_bwa_mem':BWA.bwa_mem,
            'stapler_bwa_bwasw':BWA.bwa_bwasw,
            'stapler_cutadapt':cutadapt.cutadapt,
            'stapler_fastx_toolkit_fasta_formatter':FASTX_toolkit.fasta_formatter,
            'stapler_fastx_toolkit_fasta_nucleotide_changer':FASTX_toolkit.fasta_nucleotide_changer,
            'stapler_fastx_toolkit_fastq_quality_boxplot_graph.sh':FASTX_toolkit.fastq_quality_boxplot_graph,
            'stapler_fastx_toolkit_fastq_quality_filter':FASTX_toolkit.fastq_quality_filter,
            'stapler_fastx_toolkit_fastq_quality_trimmer':FASTX_toolkit.fastq_quality_trimmer,
            'stapler_fastx_toolkit_fastq_to_fasta':FASTX_toolkit.fastq_to_fasta,
            'stapler_fastx_toolkit_fastx_artifacts_filter':FASTX_toolkit.fastx_artifacts_filter,
            'stapler_fastx_toolkit_fastx_clipper':FASTX_toolkit.fastx_clipper,
            'stapler_fastx_toolkit_fastx_collapser':FASTX_toolkit.fastx_collapser,
            'stapler_fastx_toolkit_fastx_nucleotide_distribution_graph.sh':FASTX_toolkit.fastx_nucleotide_distribution_graph,
            'stapler_fastx_toolkit_fastx_quality_stats':FASTX_toolkit.fastx_quality_stats,
            'stapler_fastx_toolkit_fastx_renamer':FASTX_toolkit.fastx_renamer,
            'stapler_fastx_toolkit_fastx_reverse_complement':FASTX_toolkit.fastx_reverse_complement,
            'stapler_fastx_toolkit_fastx_trimmer':FASTX_toolkit.fastx_trimmer,
            'stapler_fastqc':FastQC.fastqc,
            'stapler_freebayes':freebayes.freebayes,
            'stapler_psmc_fq2psmcfa':psmc.psmc_fq2psmcfa,
            'stapler_gatk_ApplyBQSR':GATK.ApplyBQSR,
            'stapler_gatk_BaseRecalibrator':GATK.BaseRecalibrator,
            'stapler_gatk_GenotypeGVCFs':GATK.GenotypeGVCFs,
            'stapler_gatk_HaplotypeCaller':GATK.HaplotypeCaller,
            'stapler_gatk_IndexFeatureFile':GATK.IndexFeatureFile,
            'stapler_psmc_history2ms':psmc.psmc_history2ms,
            'stapler_MosaikBuild':Mosaik.MosaikBuild,
            'stapler_MosaikAligner':Mosaik.MosaikAligner,
            'stapler_MosaikText':Mosaik.MosaikText,
            'stapler_PGU_vcf_allele_count_filter':PGU.PGU_vcf_allele_count_filter,
            'stapler_PGU_MAD_MAX':PGU.PGU_MAD_MAX,
            'stapler_PGU_ParalogAreaBEDmatic':PGU.PGU_ParalogAreaBEDmatic,
            'stapler_PGU_variant_density_filter':PGU.PGU_variant_density_filter,
            'stapler_PGU_vcf2fastq':PGU.PGU_vcf2fastq,
            'stapler_Picard_AddOrReplaceReadGroups':Picard.Picard_AddOrReplaceReadGroups,
            'stapler_Picard_CollectAlignmentSummaryMetrics':Picard.Picard_CollectAlignmentSummaryMetrics,
            'stapler_Picard_CollectInsertSizeMetrics': Picard.Picard_CollectInsertSizeMetrics,
            'stapler_Picard_CollectWgsMetrics':Picard.Picard_CollectWgsMetrics,
            'stapler_Picard_MarkDuplicates':Picard.Picard_MarkDuplicates,
            'stapler_Picard_SamFormatConverter':Picard.Picard_SamFormatConverter,
            'stapler_Picard_SortSam':Picard.Picard_SortSam,
            'stapler_psmc':psmc.psmc,
            'stapler_psmc_plot':psmc.psmc_plot,
            'stapler_psmc2history':psmc.psmc2history,
            'stapler_samtools_index':samtools.samtools_index,
            'stapler_samtools_rmdup':samtools.samtools_rmdup,
            'stapler_soap2':soap2.soap2,
            'stapler_tabix':tabix.tabix,
            'stapler_trimmomatic':trimmomatic.trimmomatic,
            'stapler_gzip':unix.gzip,
            'stapler_vcf_sort':misc.vcf_sort,
            'stapler_vcftools':VCFtools.VCFtools}
